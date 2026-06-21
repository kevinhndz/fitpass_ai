// app.js — Sport Fitness (versión con soporte de QR)
//
// Cambios respecto al original:
//   1. pintarTabla() añade un botón "🔁 QR" por fila.
//   2. Nueva función regenerarQR(id, nombre) que llama a POST /api/clientes/<id>/qr.
//   3. Todo lo demás (mostrar, formulario, buscar, editar, eliminar) sin cambios.

function mostrar(id) {
    const menu = document.getElementById('menu-principal');
    const reg  = document.getElementById('seccion-registro');
    const con  = document.getElementById('seccion-control');
    const rep  = document.getElementById('seccion-reportes');

    menu.style.display = 'none';
    reg.style.display = id === 'registro'  ? 'block' : 'none';
    con.style.display  = id === 'control'   ? 'block' : 'none';
    rep.style.display  = id === 'reportes'  ? 'block' : 'none';

    if (id === 'control')  traerClientes();
    if (id === 'reportes') traerReportesHoy();
}

// ── Registro de cliente ──────────────────────────────────────────────────────
const formulario = document.getElementById('formulario-registro');
if (formulario) {
    formulario.addEventListener('submit', function (e) {
        e.preventDefault();

        const btn = formulario.querySelector('button[type="submit"]');
        btn.disabled  = true;
        btn.textContent = 'Guardando...';

        const datos = {
            nombre:    document.getElementById('nombre').value,
            whatsapp:  document.getElementById('whatsapp').value,
            correo:    document.getElementById('correo').value,
            membresia: document.getElementById('membresia').value
        };

        fetch('/api/registrar', {
            method:  'POST',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(datos)
        })
        .then(r => r.json())
        .then(d => {
            alert(d.mensaje_pantalla);
            location.reload();
        })
        .catch(() => {
            alert('Error al registrar. Revisa la conexión.');
            btn.disabled    = false;
            btn.textContent = 'Guardar Cliente';
        });
    });
}

// ── Utilidades de tabla ──────────────────────────────────────────────────────
function formatearMembresia(valor) {
    const partes = valor.split('_');
    return "Mensualidad " + partes[1].charAt(0).toUpperCase() + partes[1].slice(1);
}

/**
 * pintarTabla — Renderiza filas de clientes en la tabla.
 *
 * Cambio respecto al original:
 *   Se añade un cuarto botón de acción (🔁 QR) por fila.
 *   El botón llama a regenerarQR(id, nombre).
 *   El tooltip explica su función sin necesitar texto extra en la celda.
 */
function pintarTabla(data) {
    const tbody = document.getElementById('cuerpo-tabla');
    tbody.innerHTML = '';

    if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="9" class="estado-vacio">No se encontraron clientes.</td></tr>';
        return;
    }

    data.forEach(c => {
        tbody.innerHTML += `
            <tr>
                <td>${c.id}</td>
                <td>${c.nombre}</td>
                <td>${c.telefono}</td>
                <td>${c.correo}</td>
                <td><span class="badge">${formatearMembresia(c.membresia)}</span></td>
                <td>${c.fecha_inicio}</td>
                <td>${c.fecha_vencimiento}</td>
                <td class="acciones-celda">
                    <button class="btn-icono btn-editar"
                            onclick='abrirModalEditar(${JSON.stringify(c)})'
                            aria-label="Editar ${c.nombre}"
                            title="Editar cliente">✏️</button>
                    <button class="btn-icono btn-qr"
                            onclick="regenerarQR(${c.id}, '${c.nombre.replace(/'/g, "\\'")}')"
                            aria-label="Generar QR para ${c.nombre}"
                            title="Generar y reenviar QR">🔁</button>
                    <button class="btn-icono btn-eliminar"
                            onclick="eliminarCliente(${c.id}, '${c.nombre.replace(/'/g, "\\'")}')"
                            aria-label="Eliminar ${c.nombre}"
                            title="Eliminar cliente">🗑️</button>
                </td>
            </tr>`;
    });
}

// ── Obtener / buscar clientes ────────────────────────────────────────────────
function traerClientes() {
    const campo = document.getElementById('campo-busqueda');
    if (campo) campo.value = '';
    fetch('/api/clientes')
        .then(r => r.json())
        .then(pintarTabla);
}

function buscarClientes() {
    const texto = document.getElementById('campo-busqueda').value.trim();
    if (!texto) { traerClientes(); return; }

    fetch(`/api/clientes?buscar=${encodeURIComponent(texto)}`)
        .then(r => r.json())
        .then(pintarTabla);
}

// ── Modal de edición (sin cambios) ──────────────────────────────────────────
function abrirModalEditar(cliente) {
    document.getElementById('editar-id').value        = cliente.id;
    document.getElementById('editar-nombre').value    = cliente.nombre;
    document.getElementById('editar-whatsapp').value  = cliente.telefono;
    document.getElementById('editar-correo').value    = cliente.correo;
    document.getElementById('editar-membresia').value = cliente.membresia;
    document.getElementById('modal-editar').style.display = 'flex';
}

function cerrarModal() {
    document.getElementById('modal-editar').style.display = 'none';
}

const formularioEditar = document.getElementById('formulario-editar');
if (formularioEditar) {
    formularioEditar.addEventListener('submit', function (e) {
        e.preventDefault();
        const id    = document.getElementById('editar-id').value;
        const datos = {
            nombre:    document.getElementById('editar-nombre').value,
            whatsapp:  document.getElementById('editar-whatsapp').value,
            correo:    document.getElementById('editar-correo').value,
            membresia: document.getElementById('editar-membresia').value
        };
        fetch(`/api/clientes/${id}`, {
            method:  'PUT',
            headers: { 'Content-Type': 'application/json' },
            body:    JSON.stringify(datos)
        }).then(r => r.json()).then(d => {
            cerrarModal();
            alert(d.mensaje_pantalla);
            traerClientes();
        });
    });
}

// ── Eliminar cliente (sin cambios) ───────────────────────────────────────────
function eliminarCliente(id, nombre) {
    if (!confirm(`¿Eliminar al cliente "${nombre}"? Esta acción no se puede deshacer.`)) return;

    fetch(`/api/clientes/${id}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => {
            alert(d.mensaje_pantalla);
            traerClientes();
        });
}

// ── NUEVO: Regenerar QR ───────────────────────────────────────────────────────
/**
 * regenerarQR — Llama al endpoint POST /api/clientes/<id>/qr.
 *
 * Flujo de uso típico:
 *   1. Recepcionista registra el pago en el sistema (edita la fecha de vencimiento).
 *   2. Presiona 🔁 para generar el nuevo QR con la fecha actualizada.
 *   3. El sistema envía el QR al correo y WhatsApp del cliente automáticamente.
 *
 * Por qué dos pasos en lugar de uno:
 *   Separar "registrar pago" de "generar QR" es más seguro.
 *   Si el recepcionista genera el QR antes de actualizar la fecha,
 *   el QR llevaría la fecha anterior. Con dos pasos, el orden es claro.
 */
function regenerarQR(id, nombre) {
    if (!confirm(`¿Generar y reenviar el QR para "${nombre}"?\nSe enviará al correo y WhatsApp del cliente.`)) return;

    // Feedback visual inmediato en el botón correspondiente
    const botones = document.querySelectorAll('.btn-qr');
    botones.forEach(b => {
        if (b.getAttribute('onclick').includes(`regenerarQR(${id},`)) {
            b.disabled     = true;
            b.textContent  = '⏳';
        }
    });

    fetch(`/api/clientes/${id}/qr`, { method: 'POST' })
        .then(r => r.json())
        .then(d => {
            alert(d.mensaje_pantalla);
            traerClientes();   // refresca la tabla
        })
        .catch(() => {
            alert('Error al generar el QR. Revisa la conexión con el servidor.');
            traerClientes();
        });
}

// ── Reportes de hoy (sin cambios) ────────────────────────────────────────────
function traerReportesHoy() {
    const tbody = document.getElementById('cuerpo-tabla-reportes');
    tbody.innerHTML = '<tr><td colspan="4" class="estado-vacio">Buscando cobros para hoy...</td></tr>';

    fetch('/api/reportes/hoy')
    .then(r => r.json())
    .then(data => {
        tbody.innerHTML = '';

        if (!data || data.length === 0) {
            tbody.innerHTML = '<tr><td colspan="4" class="estado-vacio" style="color: #00d68f; font-size: 16px; font-weight: bold;">¡Día libre de cobros! 🎉 Nadie vence hoy.</td></tr>';
            return;
        }

        data.forEach(c => {
            let textoMembresia = formatearMembresia(c.membresia);
            tbody.innerHTML += `
                <tr style="background-color: rgba(255, 92, 92, 0.05);">
                    <td style="padding:14px 16px;border-bottom:1px solid var(--color-borde);font-weight:bold;color:#ff5c5c;">${c.nombre}</td>
                    <td style="padding:14px 16px;border-bottom:1px solid var(--color-borde);color:white;">${c.telefono}</td>
                    <td style="padding:14px 16px;border-bottom:1px solid var(--color-borde);"><span class="badge" style="background:rgba(255,92,92,0.15);color:#ff5c5c;">${textoMembresia}</span></td>
                    <td style="padding:14px 16px;border-bottom:1px solid var(--color-borde);color:#ff5c5c;font-weight:bold;">⚠️ ${c.fecha_vencimiento}</td>
                </tr>`;
        });
    });
}