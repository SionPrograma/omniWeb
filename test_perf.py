import sys
import timeit
import inspect
sys.path.append('.')
import backend.core.permissions as p

def fake_call():
    # Creamos un frame que parezca venir de un chip
    return p._get_caller_chip()
    
# Modificamos maliciosamente el filename simulado usando un wrapper wrapper wrapper
code = fake_call.__code__
fake_call.__code__ = code.replace(co_filename='C:/Users/Propietario/Desktop/plan actual/07-proyectosGrandes/01-omniweb/chips/chip-finanzas/core/repository.py')

print("Faking Finanzas:", fake_call())
print("True root caller:", p._get_caller_chip())

ms = timeit.timeit("fake_call()", globals=globals(), number=1000) / 1000 * 1000
print(f"Performance: {ms:.4f} ms per call")
