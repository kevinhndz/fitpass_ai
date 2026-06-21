const formulario = document.getElementById('formulario-registro');

formulario.addEventListener('submit', function(evento) {
    evento.preventDefault();

    const datosCliente = {
        nombre: document.getElementById('nombre').value,
        whatsapp: document.getElementById('whatsapp').value,
        correo: document.getElementById('correo').value,
        membresia: document.getElementById('membresia').value
    };

    fetch('/api/registrar', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(datosCliente)
    })
    .then(respuesta => respuesta.json())
    .then(data => {
        alert(data.mensaje_pantalla); 
        formulario.reset();
    })
    .catch(error => {
        console.error("Error:", error);
    });
});