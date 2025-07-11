let video = null;
let canvas = null;
let capturedImages = [];

document.addEventListener('DOMContentLoaded', () => {
    video = document.getElementById('video');
    canvas = document.createElement('canvas');

    const btnRegister = document.getElementById('btnRegister');
    const btnRecognize = document.getElementById('btnRecognize');
    const formRegister = document.getElementById('formRegister');
    const registerForm = document.getElementById('registerForm');
    const cancelRegister = document.getElementById('cancelRegister');
    const captureBtn = document.getElementById('captureBtn');
    const captureCount = document.getElementById('captureCount');
    const recognitionResult = document.getElementById('recognitionResult');
    const closeRecognition = document.getElementById('closeRecognition');

    btnRegister.onclick = async () => {
        formRegister.classList.remove('hidden');
        recognitionResult.classList.add('hidden');
        btnRegister.disabled = true;
        btnRecognize.disabled = true;
        capturedImages = [];
        captureCount.textContent = '0';
        await startCamera();
    };

    cancelRegister.onclick = () => {
        formRegister.classList.add('hidden');
        btnRegister.disabled = false;
        btnRecognize.disabled = false;
        stopCamera();
    };

    captureBtn.onclick = () => {
        if (capturedImages.length >= 5) {
            alert('Maximum 5 captures reached.');
            return;
        }
        captureImage();
    };

    registerForm.onsubmit = async (e) => {
        e.preventDefault();
        if (capturedImages.length < 3) {
            alert('Please capture at least 3 images.');
            return;
        }

        const formData = new FormData(registerForm);
        const payload = {
            name: formData.get('name'),
            full_name: formData.get('full_name'),
            age: formData.get('age'),
            occupation: formData.get('occupation'),
            country: formData.get('country'),
            images: capturedImages
        };

        const res = await fetch('/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        const json = await res.json();
        alert(json.message);

        if (json.status === 'success') {
            formRegister.classList.add('hidden');
            btnRegister.disabled = false;
            btnRecognize.disabled = false;
            stopCamera();
        }
    };

    btnRecognize.onclick = async () => {
        recognitionResult.classList.add('hidden');
        formRegister.classList.add('hidden');
        btnRegister.disabled = true;
        btnRecognize.disabled = true;

        await startCamera();

        // Capture one frame after 3 seconds for recognition (adjust as needed)
        setTimeout(async () => {
            const imgData = captureImage();
            const res = await fetch('/recognize', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ image: imgData })
            });
            const json = await res.json();
            if (json.status === 'success') {
                showRecognition(json);
            } else {
                alert(json.message || 'Face not recognized.');
                btnRegister.disabled = false;
                btnRecognize.disabled = false;
                stopCamera();
            }
        }, 3000);
    };

    closeRecognition.onclick = () => {
        recognitionResult.classList.add('hidden');
        btnRegister.disabled = false;
        btnRecognize.disabled = false;
        stopCamera();
    };

});

async function startCamera() {
    if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia) {
        const stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'user' } });
        video.srcObject = stream;
        return new Promise(resolve => {
            video.onloadedmetadata = () => { video.play(); resolve(); };
        });
    } else {
        alert('Camera not supported on this browser/device.');
    }
}

function stopCamera() {
    if (video.srcObject) {
        video.srcObject.getTracks().forEach(track => track.stop());
        video.srcObject = null;
    }
}

function captureImage() {
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    const dataURL = canvas.toDataURL('image/png');
    capturedImages.push(dataURL);
    document.getElementById('captureCount').textContent = capturedImages.length;
    return dataURL;
}

function showRecognition(data) {
    const recognitionResult = document.getElementById('recognitionResult');
    recognitionResult.classList.remove('hidden');

    document.getElementById('profileImage').src = data.id_image || '';
    document.getElementById('resFullName').textContent = data.info['Full Name'] || '';
    document.getElementById('resAge').textContent = data.info['Age'] || '';
    document.getElementById('resOccupation').textContent = data.info['Occupation'] || '';
    document.getElementById('resCountry').textContent = data.info['Country'] || '';

    stopCamera();
}
