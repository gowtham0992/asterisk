"""Original synthetic fixtures. These are illustrative, not historical research findings."""
def example(kind='overlap'):
    metadata = 'capture,subject\n'
    split = 'capture,partition\n'
    for i in range(1, 121):
        split += f'frame_{i:04d},' + ('train' if i <= 80 else 'test') + '\n'
        subject = i if i <= 80 or kind != 'overlap' else (i-80 if i <= 96 else i)
        metadata += f'frame_{i:04d},specimen_{subject:04d}\n'
    docs = ('# Specimen recognition study\n\nWe evaluate generalization to specimens not observed during training.\n'
            'In splits.csv, capture is the unique image identifier and partition is train or test.\n'
            'In specimens.csv, capture links each image to subject, the persistent specimen identifier.\n'
            'Different captures may depict the same specimen. The test set should contain only specimens absent from train.\n'
            'This is an original synthetic example, not a real study or a measured model-performance result.\n')
    files = [{'name':'splits.csv','content':split}, {'name':'README.md','content':docs}]
    if kind != 'missing':
        files.append({'name':'specimens.csv','content':metadata})
    return {'title': {'overlap':'Specimen study · overlapping split','clean':'Specimen study · independent split',
                      'missing':'Specimen study · missing mapping'}[kind],
            'claim':'The model generalizes to specimens not seen during training.', 'files':files}
