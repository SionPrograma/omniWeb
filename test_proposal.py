import asyncio
import os
import sys

# Agregar la ruta del proyecto al sys.path
omniweb_path = r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb'
if omniweb_path not in sys.path:
    sys.path.append(omniweb_path)

from backend.core.ai_host.processors.proposal_processor import ProposalProcessor
async def main():
    processor = ProposalProcessor()
    
    # Path de prueba
    test_file = r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\backend\core\ai_host\brain_router.py'
    
    # Contexto simulado para que no falle buscando path
    context = {'multimodal_evidence': [{'type': 'current_file', 'path': test_file}]}

    print('=== PRUEBA A: CAMBIO PEQUEÑO ===')
    try:
        msg_a = 'agregá un comentario al inicio'
        res_a = await processor.process(msg_a, context)
        print(res_a.message)
    except Exception as e:
        print(f"Error A: {e}")
    print('\n')

    print('=== PRUEBA B: MICROFIX LOCAL ===')
    try:
        msg_b = 'proponé un microfix para esta función'
        res_b = await processor.process(msg_b, context)
        print(res_b.message)
    except Exception as e:
        print(f"Error B: {e}")
    print('\n')

    print('=== PRUEBA C: PEDIDO AMBIGUO O RIESGOSO ===')
    try:
        msg_c = 'arreglá este archivo'
        res_c = await processor.process(msg_c, context)
        print(res_c.message)
    except Exception as e:
        print(f"Error C: {e}")
    print('\n')

if __name__ == '__main__':
    asyncio.run(main())
