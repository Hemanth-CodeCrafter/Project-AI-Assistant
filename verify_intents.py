from core.intent_classifier import classify, classify_all

samples = [
    'yt',
    'yt search',
    'search on youtube',
    'find on youtube',
    'play on youtube',
    'youtube search',
    'search youtube',
    'google',
    'chrome',
    'spotify',
    'maps',
    'calculator',
    'notepad',
    'vscode',
]

for sample in samples:
    print(sample, '->', classify(sample)[0])

print('---')
print(classify_all('search on youtube'))
