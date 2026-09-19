"""Persistent, locked reservation ledger for estimated token charges.

One batch process at a time. Unknown/failed response usage retains its entire
reservation instead of assuming it was free. Prices are the report's rates,
so this is an estimated ceiling, not a guarantee about provider billing.
"""
import json,threading,uuid
class Budget:
    def __init__(self,path,rates,limit=10.0,initial=0):
        self.path=path;self.rates=rates;self.lock=threading.Lock()
        self.state=json.loads(path.read_text()) if path.exists() else {'limit_usd':limit,'settled_usd':initial,'reservations':{},'uncertain':[]}
        self.save()
    def save(self):
        tmp=self.path.with_suffix('.tmp');tmp.write_text(json.dumps(self.state,indent=2));tmp.replace(self.path)
    def reserve(self,model,prompt,completion):
        rate=self.rates[model];amount=(prompt*rate[0]+completion*rate[1])/1e6
        with self.lock:
            used=self.state['settled_usd']+sum(r['amount'] for r in self.state['reservations'].values())
            if used+amount>self.state['limit_usd']:return None
            id=uuid.uuid4().hex;self.state['reservations'][id]={'amount':amount,'rates':rate};self.save();return id
    def settle(self,id,prompt,completion):
        with self.lock:
            reservation=self.state['reservations'].pop(id);rate=reservation['rates']
            self.state['settled_usd']+=(prompt*rate[0]+completion*rate[1])/1e6
            self.save()
    def uncertain(self,id):
        with self.lock:self.state['uncertain'].append(id);self.save()
