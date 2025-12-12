from redislite import Redis

r = Redis()
r.set('foo', 'bar')
print(r.get('foo'))
