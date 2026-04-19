import os
import asyncio
import logging
import vertexai

from dotenv import load_dotenv
from google.adk.sessions import InMemorySessionService

print("✅ ALL LIBRARIES ARE LOADED AND READY TO GO!")




# <-----  I.    CONFIGURE LOGGING  ------>

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("agent_without_memory.log"),
        logging.StreamHandler()
    ],
    force=True  # Ensure that logging configuration is applied even if logging was previously configured
)

logger = logging.getLogger(__name__)

print("✅ LOGGERS ARE CONFIGURED, LOADED AND READY TO GO!")




# <-----  II.   LOAD/INIT ENVIRNONMENT VARIABLES  ------>

load_dotenv()
PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("REGION", "us-central1")

if PROJECT_ID:
    vertexai.init(project=PROJECT_ID, location=LOCATION)
else:
    logger.error("No project id is found. AI features will be disabled.")

session_service = InMemorySessionService()
my_user_id = "adk_adventurer_007"

print("✅ ALL ENVIRONMENT VARIABLES ARE LOADED AND READY TO GO!")



# <-----  III.   DEFINE THE SPECIALIST AGENTS  ------>

from agent_query import run_agent_query
from agents import create_multi_day_trip_agent

multi_day_trip_agent = create_multi_day_trip_agent()
print("✅ SPECIALIST AGENT IS LOADED AND READY TO GO!")




# <-----  IV.   TEST THE ADAPTIVE-PLANNER-WITHOUT-MEMORY AGENT  ------>

async def run_memory_failure_demo() -> None:
    print("\n" + "#"*60)
    print("AGENT THAT FAILS TO ADAPT MEMORY FROM THE SESSION.")
    print("#"*60)
    
    # (Turn 1) The user initiates the trip with session_one
    query1 = "hi! I want to plan a 2-day trip to Guadalajara, Mexico. I'm interested in the country's history and the local food."
    session_one = await session_service.create_session(app_name=multi_day_trip_agent.name, user_id=my_user_id)
    await run_agent_query(multi_day_trip_agent, query1, session_one, my_user_id, session_service)


    # (Turn 2) The user ask to continue but in a seperate new session
    query2 = "That sounds great! Please plan Day 2 now, keeping my preferences in mind."
    session_two = await session_service.create_session(app_name=multi_day_trip_agent.name, user_id=my_user_id)
    await run_agent_query(multi_day_trip_agent, query2, session_two, my_user_id, session_service)




if __name__ == "__main__":
    asyncio.run(run_memory_failure_demo())





"""
✅ FINAL RESPONSE:
¡Hola! Qué emoción que quieras explorar Guadalajara. Es una ciudad fantástica para la historia y la gastronomía.

Vamos a empezar con el primer día de tu viaje. Aquí tienes una propuesta que combina historia y deliciosa comida local:

**Día 1: Corazón Histórico y Sabores Tradicionales**

*   **Mañana (9:00 AM - 1:00 PM): Centro Histórico y Arquitectura Colonial**
    *   Comienza tu día en el corazón de Guadalajara, visitando la impresionante **Catedral Metropolitana**.
    *   Luego, dirígete al **Palacio de Gobierno**, conocido por sus murales de José Clemente Orozco que narran la historia de México.
    *   Pasea por la **Plaza de Armas** y la **Plaza de los Fundadores**, absorbiendo la atmósfera histórica.
*   **Almuerzo (1:00 PM - 2:30 PM): Sabor Tapatío**
    *   Disfruta de un almuerzo tradicional en un restaurante cercano al centro histórico. Te sugiero probar platillos icónicos de Guadalajara como las **tortas ahogadas** o la **birria**.
*   **Tarde (2:30 PM - 6:00 PM): Arte e Historia en un Edificio Emblemático**
    *   Visita el **Instituto Cultural Cabañas**, declarado Patrimonio de la Humanidad por la UNESCO. Este antiguo hospicio es una joya arquitectónica y alberga más murales impactantes de Orozco.
*   **Noche (7:00 PM en adelante): Cena con Tradición**
    *   Para la cena, te propongo un lugar que ofrezca música de mariachi en vivo y platillos mexicanos auténticos para una experiencia inmersiva.

¿Qué te parece este primer día? ¿Hay algo que te gustaría cambiar o explorar más a fondo?


✅ FINAL RESPONSE:
It sounds like we had a great plan for Day 1! To help me plan a fantastic Day 2 that builds on our previous discussion and your preferences, could you please remind me of:

*   Our destination?
*   Your main interests for this trip? (e.g., history, food, adventure, relaxation)
*   What we planned for Day 1? (A brief summary will do!)

Once I have those details, I'll be happy to craft an exciting itinerary for Day 2!


"""