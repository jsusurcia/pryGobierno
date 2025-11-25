# 🚀 Guía Rápida de Instalación - Módulo de Predicciones IA

## ⚡ Instalación en 3 Pasos

### Paso 1: Instalar Dependencias

Ejecuta en tu terminal:

```bash
pip install pandas scikit-learn scipy
```

**Nota**: `numpy` ya está instalado (es requerido por biometría facial).

### Paso 2: Verificar Base de Datos

El módulo funciona con los datos existentes en tu base de datos. No requiere tablas adicionales.

**Tablas utilizadas**:
- ✅ `INCIDENTE`
- ✅ `CATEGORIA`
- ✅ `USUARIO`
- ✅ `ROL`
- ✅ `EQUIPO_TECNICO`

### Paso 3: Reiniciar Aplicación

```bash
python app/run.py
```

---

## 🎯 Primer Uso

1. **Inicia sesión** como **Jefe de TI** (id_rol = 1)

2. En el menú lateral, haz clic en **"Predicciones IA"**

3. ¡Listo! El dashboard cargará automáticamente todas las predicciones

---

## 📊 Requisitos Mínimos de Datos

Para obtener predicciones útiles, necesitas:

- ✅ **Mínimo 2 meses** de incidentes registrados
- ✅ **Al menos 30 incidentes** en total
- ✅ Incidentes con **fechas válidas**
- ✅ Algunos incidentes **resueltos** (para MTTR)

**Nota**: Si tienes menos datos, el módulo funcionará pero mostrará mensajes de "datos insuficientes" en algunas secciones.

---

## ⚠️ Solución Rápida de Problemas

### "No hay suficientes datos históricos"
➡️ **Solución**: Reduce el período de análisis a 1 mes en los filtros

### Las dependencias no se instalan
➡️ **Solución**: Actualiza pip primero:
```bash
python -m pip install --upgrade pip
pip install pandas scikit-learn scipy
```

### Error 403 (Sin permisos)
➡️ **Solución**: Verifica que estás logueado como Jefe de TI (id_rol = 1)

### Los gráficos no aparecen
➡️ **Solución**: Verifica tu conexión a internet (usa CDN de Chart.js)

---

## 📦 Archivos Creados/Modificados

### Nuevos archivos:
- ✅ `app/controllers/control_predicciones.py` - Lógica de IA
- ✅ `app/templates/predicciones_ia.html` - Interfaz visual
- ✅ `MODULO_PREDICCIONES_IA.md` - Documentación completa
- ✅ `INSTALACION_PREDICCIONES.md` - Esta guía

### Archivos modificados:
- ✅ `app/run.py` - Agregadas 7 rutas nuevas
- ✅ `app/templates/sidebar.html` - Agregado enlace al menú
- ✅ `requirements.txt` - Agregadas dependencias ML

---

## 🧪 Verificar Instalación

Ejecuta este código en Python para verificar que todo está correcto:

```python
# Verificar importaciones
try:
    import numpy as np
    import pandas as pd
    from sklearn import __version__ as sklearn_version
    print("✅ Todas las dependencias instaladas correctamente")
    print(f"   NumPy: {np.__version__}")
    print(f"   Pandas: {pd.__version__}")
    print(f"   Scikit-learn: {sklearn_version}")
except ImportError as e:
    print(f"❌ Error: {e}")
    print("   Ejecuta: pip install pandas scikit-learn scipy")
```

---

## 🎓 Próximos Pasos

1. **Lee la documentación completa**: `MODULO_PREDICCIONES_IA.md`
2. **Explora el dashboard**: Familiarízate con cada sección
3. **Ajusta filtros**: Prueba diferentes períodos de análisis
4. **Toma decisiones**: Usa las recomendaciones para mejorar tu gestión

---

## 📞 ¿Necesitas Ayuda?

Consulta la documentación completa en `MODULO_PREDICCIONES_IA.md` para:
- 📖 Explicación detallada de cada algoritmo
- 🔧 Configuración avanzada
- 💡 Casos de uso reales
- 🐛 Solución de problemas extendida

---

**¡Disfruta de tu nuevo módulo de Predicciones con IA! 🚀🤖**

