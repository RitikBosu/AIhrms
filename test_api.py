import requests

r = requests.post('http://localhost:8001/api/auth/login', json={'email': 'admin@fwc.demo', 'password': 'Admin@123'})
token = r.json()['token']
h = {'Authorization': 'Bearer ' + token}

tests = [
    ('HR  - Login',        r),
    ('HR  - Employees',    requests.get('http://localhost:8001/api/employees',   headers=h)),
    ('HR  - Dashboard',    requests.get('http://localhost:8001/api/dashboard',   headers=h)),
    ('HR  - Attendance',   requests.get('http://localhost:8001/api/attendance',  headers=h)),
    ('HR  - Leaves',       requests.get('http://localhost:8001/api/leaves',      headers=h)),
    ('HR  - Payroll',      requests.get('http://localhost:8001/api/payroll',     headers=h)),
    ('HR  - Performance',  requests.get('http://localhost:8001/api/performance', headers=h)),
    ('AI  - Candidates',   requests.get('http://localhost:8002/api/candidates',  headers=h)),
    ('AI  - JD',           requests.get('http://localhost:8002/api/jd',          headers=h)),
]

print()
all_pass = True
for name, resp in tests:
    ok = resp.status_code == 200
    if not ok:
        all_pass = False
    body = resp.json()
    size = str(len(body)) if isinstance(body, list) else ''
    status = 'PASS' if ok else 'FAIL'
    print('  [' + status + '] ' + name + ': ' + str(resp.status_code) + ' ' + size)

print()
print('Result: ' + ('ALL TESTS PASSED' if all_pass else 'SOME TESTS FAILED'))
