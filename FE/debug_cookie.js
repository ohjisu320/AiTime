
fetch('http://70.12.246.92:8080/api/v1/user/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ loginId: 'guest1234', password: 'guest1234' })
}).then(res => {
    console.log('Status:', res.status);
    console.log('Headers:');
    res.headers.forEach((val, key) => console.log(`${key}: ${val}`));
}).catch(err => console.error(err));
