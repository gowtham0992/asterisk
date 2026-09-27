"""Cost reservation adapter for a single request; never retries a provider call."""
import json
import math


class CompletionFailure(RuntimeError):
    def __init__(self, message, *, response=None, reservation=None, estimated_usd=0):
        super().__init__(message)
        self.provider_response = response
        self.reservation = reservation
        self.estimated_usd = estimated_usd


class BudgetedCompletion:
    def __init__(self, budget, model, starting_committed, request, incremental_cap=1.0):
        if not math.isfinite(starting_committed) or starting_committed < 0:
            raise ValueError('Invalid original cost baseline')
        if not math.isfinite(incremental_cap) or not 0 < incremental_cap <= 1:
            raise ValueError('Cannot expand the original extraction cap')
        self.budget, self.model, self.start = budget, model, starting_committed
        self.request, self.cap = request, incremental_cap
        self.exhausted = False

    def __call__(self, messages, maximum, timeout):
        if self.exhausted:
            raise CompletionFailure('Provider previously exceeded the reserved usage bounds')
        if type(maximum) is not int or not 1 <= maximum <= 4000 or not 0 < timeout <= 60:
            raise ValueError('Invalid request bounds')
        upper = len(json.dumps(messages, ensure_ascii=False).encode()) + 128
        prompt_rate, completion_rate = self.budget.rates[self.model]
        reserve_cost = (upper * prompt_rate + maximum * completion_rate) / 1e6
        committed = self.budget.state['settled_usd'] + sum(r['amount'] for r in self.budget.state['reservations'].values())
        if committed < self.start or committed - self.start + reserve_cost > self.cap:
            raise CompletionFailure('Original cumulative extraction cap reached or ledger inconsistent')
        reservation = self.budget.reserve(self.model, upper, maximum)
        if not reservation:
            raise CompletionFailure('Global estimated cost cap reached')
        response = None
        known_cost = 0
        try:
            response = self.request(messages=messages, maximum=maximum, timeout=timeout)
            if not isinstance(response, dict):
                raise ValueError('Invalid provider response')
            usage = response.get('usage') or {}
            prompt, completion = usage.get('prompt_tokens'), usage.get('completion_tokens')
            if any(type(x) is not int or x < 0 for x in (prompt, completion)):
                raise ValueError('Missing or invalid provider usage')
            # Known usage is charged even if the response content is invalid.
            self.budget.settle(reservation, prompt, completion)
            known_cost = (prompt * prompt_rate + completion * completion_rate) / 1e6
            if prompt > upper or completion > maximum:
                self.exhausted = True
                raise ValueError('Provider exceeded reserved usage bounds; further calls disabled')
            content = response['choices'][0]['message']['content']
            if not isinstance(content, str):
                raise ValueError('Missing text completion')
            return {'content': content, 'response': response, 'prompt_tokens': prompt,
                    'completion_tokens': completion,
                    'estimated_usd': (prompt * prompt_rate + completion * completion_rate) / 1e6}
        except Exception as exc:
            if reservation in self.budget.state['reservations']:
                self.budget.uncertain(reservation)
            raise CompletionFailure(type(exc).__name__ + ': ' + str(exc),
                                    response=response, reservation=reservation, estimated_usd=known_cost) from exc
