
// ── Navegación ───────────────────────────────────────────────────────────────
function mostrar(id) {
    const menu = document.getElementById('menu-principal');
    const reg  = document.getElementById('seccion-registro');
    const con  = document.getElementById('seccion-control');
    const rep  = document.getElementById('seccion-reportes');

    menu.style.display = 'none';
    reg.style.display  = id === 'registro' ? 'block' : 'none';
    con.style.display  = id === 'control'  ? 'block' : 'none';
    rep.style.display  = id === 'reportes' ? 'block' : 'none';

    if (id === 'control')  traerClientes();
    if (id === 'reportes') traerReportesHoy();
}

// ── Registro de cliente ──────────────────────────────────────────────────────
const formulario = document.getElementById('formulario-registro');
if (formulario) {
    formulario.addEventListener('submit', function (e) {
        e.preventDefault();

        const btn = formulario.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.classList.add('cargando');

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
            btn.disabled = false;
            btn.classList.remove('cargando');
        });
    });
}

// ── Utilidades ───────────────────────────────────────────────────────────────
function formatearMembresia(valor) {
    const partes = valor.split('_');
    return 'Mensualidad ' + partes[1].charAt(0).toUpperCase() + partes[1].slice(1);
}


function estadoVencimiento(fechaStr) {
    const hoy   = new Date();
    hoy.setHours(0, 0, 0, 0);
    const vence = new Date(fechaStr + 'T00:00:00');
    const dias  = Math.round((vence - hoy) / (1000 * 60 * 60 * 24));

    if (dias < 0)  return { clase: 'estado-vencido', badgeClase: 'badge-vencido', badgeTexto: `Vencido (${Math.abs(dias)}d)` };
    if (dias === 0) return { clase: 'estado-hoy',    badgeClase: 'badge-hoy',     badgeTexto: 'Vence hoy ⚠️' };
    if (dias <= 5)  return { clase: 'estado-pronto', badgeClase: 'badge-pronto',  badgeTexto: `Vence en ${dias}d` };
    return              { clase: 'estado-ok',     badgeClase: '',              badgeTexto: '' };
}

// ── Pintar tabla ─────────────────────────────────────────────────────────────
function pintarTabla(data) {
    const tbody = document.getElementById('cuerpo-tabla');
    tbody.innerHTML = '';

    if (!data.length) {
        tbody.innerHTML = '<tr><td colspan="8" class="estado-vacio">No se encontraron clientes.</td></tr>';
        return;
    }

    data.forEach(c => {
        const ev = estadoVencimiento(c.fecha_vencimiento);

        // Badge de membresía
        const badgeMembresia = `<span class="badge">${formatearMembresia(c.membresia)}</span>`;

        // Badge de estado (solo si no es "ok")
        const badgeEstado = ev.badgeTexto
            ? `<span class="badge ${ev.badgeClase}" style="margin-left:6px;font-size:10px;">${ev.badgeTexto}</span>`
            : '';

        tbody.innerHTML += `
            <tr class="${ev.clase}">
                <td><span style="color:var(--texto-2);font-family:'JetBrains Mono',monospace;font-size:13px;">#${c.id}</span></td>
                <td style="font-weight:600;">${c.nombre}</td>
                <td style="color:var(--texto-2);">${c.telefono}</td>
                <td style="color:var(--texto-2);font-size:13px;">${c.correo}</td>
                <td>${badgeMembresia}</td>
                <td style="color:var(--texto-2);font-size:13px;">${c.fecha_inicio}</td>
                <td>${c.fecha_vencimiento}${badgeEstado}</td>
                <td class="acciones-celda">
                    <button class="btn-icono btn-editar"
                            onclick='abrirModalEditar(${JSON.stringify(c)})'
                            aria-label="Editar ${c.nombre}"
                            title="Editar cliente">✏️</button>
                    <button class="btn-icono btn-qr"
                            id="btn-qr-${c.id}"
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

// ── Modal de edición ─────────────────────────────────────────────────────────
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
        const btn   = formularioEditar.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.classList.add('cargando');

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
        })
        .then(r => r.json())
        .then(d => {
            cerrarModal();
            alert(d.mensaje_pantalla);
            traerClientes();
        })
        .finally(() => {
            btn.disabled = false;
            btn.classList.remove('cargando');
        });
    });
}

// ── Eliminar cliente ─────────────────────────────────────────────────────────
function eliminarCliente(id, nombre) {
    if (!confirm(`¿Eliminar al cliente "${nombre}"? Esta acción no se puede deshacer.`)) return;

    fetch(`/api/clientes/${id}`, { method: 'DELETE' })
        .then(r => r.json())
        .then(d => {
            alert(d.mensaje_pantalla);
            traerClientes();
        });
}

// ── Regenerar QR ─────────────────────────────────────────────────────────────
function regenerarQR(id, nombre) {
    if (!confirm(`¿Generar y reenviar el QR para "${nombre}"?\nSe enviará al correo y WhatsApp del cliente.`)) return;

    // Feedback visual: spinner en el botón exacto de esta fila
    const btn = document.getElementById(`btn-qr-${id}`);
    if (btn) {
        btn.disabled   = true;
        btn.textContent = '⏳';
        btn.title       = 'Generando QR...';
    }

    fetch(`/api/clientes/${id}/qr`, { method: 'POST' })
        .then(r => r.json())
        .then(d => {
            alert(d.mensaje_pantalla);
            traerClientes();
        })
        .catch(() => {
            alert('Error al generar el QR. Revisa la conexión con el servidor.');
            traerClientes();
        });
}

// ── Reportes de hoy ──────────────────────────────────────────────────────────
function traerReportesHoy() {
    const tbody = document.getElementById('cuerpo-tabla-reportes');
    tbody.innerHTML = '<tr><td colspan="4" class="estado-vacio">Buscando cobros para hoy...</td></tr>';

    fetch('/api/reportes/hoy')
    .then(r => r.json())
    .then(data => {
        tbody.innerHTML = '';

        if (!data || data.length === 0) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" class="estado-vacio" style="color:var(--verde);font-size:16px;font-weight:700;">
                        ¡Día libre de cobros! 🎉 Nadie vence hoy.
                    </td>
                </tr>`;
            return;
        }

        data.forEach(c => {
            tbody.innerHTML += `
                <tr>
                    <td style="padding:16px 18px;border-bottom:1px solid rgba(255,255,255,0.06);font-weight:700;color:#ff4d6d;">${c.nombre}</td>
                    <td style="padding:16px 18px;border-bottom:1px solid rgba(255,255,255,0.06);color:#f0f0f8;">${c.telefono}</td>
                    <td style="padding:16px 18px;border-bottom:1px solid rgba(255,255,255,0.06);">
                        <span class="badge badge-vencido">${formatearMembresia(c.membresia)}</span>
                    </td>
                    <td style="padding:16px 18px;border-bottom:1px solid rgba(255,255,255,0.06);color:#ff4d6d;font-weight:700;">⚠️ ${c.fecha_vencimiento}</td>
                </tr>`;
        });
    });
}