(function () {
    const canvas = document.getElementById('shader-canvas');
    if (!canvas) return;

    function syncSize() {
        canvas.width  = window.innerWidth;
        canvas.height = window.innerHeight;
    }
    window.addEventListener('resize', syncSize);
    syncSize();

    const gl = canvas.getContext('webgl') || canvas.getContext('experimental-webgl');
    if (!gl) return;

    const vs = `
        attribute vec2 a_pos;
        varying vec2 v_uv;
        void main(){ v_uv = a_pos*.5+.5; gl_Position=vec4(a_pos,0,1); }`;

    const fs = `
        precision highp float;
        uniform float u_time;
        uniform vec2  u_res;
        uniform vec2  u_mouse;
        varying vec2  v_uv;
        void main(){
            vec2 uv    = v_uv;
            vec2 mouse = u_mouse / u_res;
            vec3 orange = vec3(1.,.48,.24);
            vec3 green  = vec3(0.,.9,.63);
            vec3 red    = vec3(1.,.29,.32);
            vec3 col    = vec3(.03,.03,.04);
            float m1 = smoothstep(.7,.1,distance(uv,vec2(.15,.2)+.12*vec2(sin(u_time*.4),cos(u_time*.5))));
            float m2 = smoothstep(.7,.1,distance(uv,vec2(.85,.3)+.12*vec2(cos(u_time*.5),sin(u_time*.3))));
            float m3 = smoothstep(.7,.1,distance(uv,vec2(.5,.75)+.10*vec2(sin(u_time*.6),cos(u_time*.2))));
            float mg = smoothstep(.45,.0,distance(uv,mouse))*.2;
            col += orange*m1*.18 + green*m2*.14 + red*m3*.12 + green*mg*.5;
            col += sin(uv.y*1200.)*.008;
            gl_FragColor = vec4(col,.6);
        }`;

    function mkShader(type, src) {
        const s = gl.createShader(type);
        gl.shaderSource(s, src);
        gl.compileShader(s);
        return s;
    }

    const prog = gl.createProgram();
    gl.attachShader(prog, mkShader(gl.VERTEX_SHADER, vs));
    gl.attachShader(prog, mkShader(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(prog);
    gl.useProgram(prog);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1,1,-1,-1,1,1,1]), gl.STATIC_DRAW);
    const pos = gl.getAttribLocation(prog, 'a_pos');
    gl.enableVertexAttribArray(pos);
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0);

    const uTime  = gl.getUniformLocation(prog, 'u_time');
    const uRes   = gl.getUniformLocation(prog, 'u_res');
    const uMouse = gl.getUniformLocation(prog, 'u_mouse');

    let mx = canvas.width / 2, my = canvas.height / 2;
    window.addEventListener('mousemove', e => {
        mx = e.clientX;
        my = window.innerHeight - e.clientY;
    });

    function render(t) {
        syncSize();
        gl.viewport(0, 0, canvas.width, canvas.height);
        gl.uniform1f(uTime,  t * .001);
        gl.uniform2f(uRes,   canvas.width, canvas.height);
        gl.uniform2f(uMouse, mx, my);
        gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4);
        requestAnimationFrame(render);
    }
    render(0);
})();


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

// ── Toggle de campos de fecha para migración ─────────────────────────────────
function toggleFechasMigracion() {
    const checked = document.getElementById('es_migracion').checked;
    const campos  = document.getElementById('campos-migracion');
    campos.style.display = checked ? 'block' : 'none';

    // Si se desmarca, limpiamos las fechas para no arrastrar valores viejos
    if (!checked) {
        document.getElementById('fecha_inicio').value = '';
        document.getElementById('fecha_vencimiento').value = '';
    }
}

// ── Registro de cliente ──────────────────────────────────────────────────────
const formulario = document.getElementById('formulario-registro');
if (formulario) {
    formulario.addEventListener('submit', function (e) {
        e.preventDefault();

        const esMigracion = document.getElementById('es_migracion').checked;

        // Validación: si es migración, las dos fechas son obligatorias
        if (esMigracion) {
            const fi = document.getElementById('fecha_inicio').value;
            const fv = document.getElementById('fecha_vencimiento').value;
            if (!fi || !fv) {
                alert('Para un cliente migrado debes ingresar la fecha de pago y la fecha de vencimiento del papel.');
                return;
            }
        }

        const btn = formulario.querySelector('button[type="submit"]');
        btn.disabled = true;
        btn.classList.add('cargando');

        const datos = {
            nombre:            document.getElementById('nombre').value,
            whatsapp:          document.getElementById('whatsapp').value,
            correo:            document.getElementById('correo').value,
            membresia:         document.getElementById('membresia').value,
            // Solo se envían fechas si es migración; si es cliente nuevo,
            // se mandan vacías y el backend calcula hoy + 30 días automáticamente.
            fecha_inicio:      esMigracion ? document.getElementById('fecha_inicio').value : '',
            fecha_vencimiento: esMigracion ? document.getElementById('fecha_vencimiento').value : ''
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

    if (dias < 0)   return { clase: 'estado-vencido', badgeClase: 'badge-vencido', badgeTexto: `Vencido (${Math.abs(dias)}d)` };
    if (dias === 0) return { clase: 'estado-hoy',     badgeClase: 'badge-hoy',     badgeTexto: 'Vence hoy ⚠️' };
    if (dias <= 5)  return { clase: 'estado-pronto',  badgeClase: 'badge-pronto',  badgeTexto: `Vence en ${dias}d` };
    return                 { clase: 'estado-ok',      badgeClase: '',              badgeTexto: '' };
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

        const badgeMembresia = `<span class="badge">${formatearMembresia(c.membresia)}</span>`;
        const badgeEstado    = ev.badgeTexto
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
        const id  = document.getElementById('editar-id').value;
        const btn = formularioEditar.querySelector('button[type="submit"]');
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

    const btn = document.getElementById(`btn-qr-${id}`);
    if (btn) {
        btn.disabled    = true;
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