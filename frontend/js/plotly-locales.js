// Plotly Locales - Traducciones para los tooltips del gráfico

// Español
Plotly.register({
    moduleType: 'locale',
    name: 'es',
    dictionary: {
        'Autoscale': 'Autoescala',
        'Box Select': 'Selección de caja',
        'Click to enter Colorscale title': 'Título de escala de color',
        'Click to enter Plot title': 'Título del gráfico',
        'Click to enter X axis title': 'Título del eje X',
        'Click to enter Y axis title': 'Título del eje Y',
        'Compare data on hover': 'Comparar datos al pasar',
        'Double-click to zoom back out': 'Doble clic para alejar',
        'Download plot as a png': 'Descargar gráfico como PNG',
        'Download plot': 'Descargar gráfico',
        'Edit in Chart Studio': 'Editar en Chart Studio',
        'Lasso Select': 'Selección de lazo',
        'Orbital rotation': 'Rotación orbital',
        'Pan': 'Desplazar',
        'Produced with Plotly': 'Hecho con Plotly',
        'Reset': 'Restablecer',
        'Reset axes': 'Restablecer ejes',
        'Reset camera to default': 'Restablecer cámara',
        'Reset view': 'Restablecer vista',
        'Show closest data on hover': 'Mostrar datos cercanos',
        'Snapshot success': 'Captura exitosa',
        'Sorry, there was a problem downloading your snapshot!': 'Error al descargar',
        'Taking snapshot - this may take a few seconds': 'Capturando imagen...',
        'Toggle Spike Lines': 'Alternar líneas',
        'Turntable rotation': 'Rotación giratoria',
        'Zoom': 'Zoom',
        'Zoom in': 'Acercar',
        'Zoom out': 'Alejar',
        'close:': 'cierre:',
        'trace': 'traza',
        'lat:': 'lat:',
        'lon:': 'lon:',
        'max:': 'máx:',
        'mean:': 'media:',
        'median:': 'mediana:',
        'min:': 'mín:',
        'new text': 'nuevo texto'
    },
    format: {
        days: ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'],
        shortDays: ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'],
        months: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
        shortMonths: ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'],
        date: '%d/%m/%Y'
    }
});

// Inglés
Plotly.register({
    moduleType: 'locale',
    name: 'en',
    dictionary: {}, // Deja esto vacío, Plotly usa su inglés interno
    format: {
        days: ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday'],
        shortDays: ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        months: ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'],
        shortMonths: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        date: '%m/%d/%Y'
    }
});

// Euskera
Plotly.register({
    moduleType: 'locale',
    name: 'eu',
    dictionary: {
        'Autoscale': 'Autoeskala',
        'Box Select': 'Kutxa hautapena',
        'Download plot as a png': 'Deskargatu grafikoa PNG gisa',
        'Download plot': 'Deskargatu grafikoa',
        'Lasso Select': 'Lazo hautapena',
        'Pan': 'Mugitu',
        'Reset': 'Berrezarri',
        'Reset axes': 'Berrezarri ardatzak',
        'Show closest data on hover': 'Erakutsi datu hurbilenak', // Corregido el carácter 'к'
        'Zoom': 'Zoom',
        'Zoom in': 'Hurbildu',
        'Zoom out': 'Urrundu'
    },
    format: {
        days: ['Igandea', 'Astelehena', 'Asteartea', 'Asteazkena', 'Osteguna', 'Ostirala', 'Larunbata'],
        shortDays: ['Ig', 'Al', 'Ar', 'Az', 'Og', 'Or', 'Lr'],
        months: ['Urtarrila', 'Otsaila', 'Martxoa', 'Apirila', 'Maiatza', 'Ekaina', 'Uztaila', 'Abuztua', 'Iraila', 'Urria', 'Azaroa', 'Abendua'],
        shortMonths: ['Urt', 'Ots', 'Mar', 'Api', 'Mai', 'Eka', 'Uzt', 'Abu', 'Ira', 'Urr', 'Aza', 'Abe'],
        date: '%Y/%m/%d'
    }
});

console.log('[RMN] Plotly locales loaded (es, en, eu) - CLEANED');