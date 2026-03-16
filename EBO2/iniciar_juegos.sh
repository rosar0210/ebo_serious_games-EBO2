#!/bin/bash
pkill -f "python3 generated/therapistPanel.py"  # Limpia procesos colgados

export ROBOCOMP=/opt/robocomp # para evitar logs incomodos

# Obtener la ruta del directorio donde se encuentra el script
BASE_DIR="$(dirname "$(realpath "$0")")"

# Ejecutar primero python3 reiniciar.py y esperar 1 segundo
python3 "$BASE_DIR/reiniciar.py"
sleep 1

# Definir las rutas y los nombres de los scripts a ejecutar
declare -A rutas
declare -A scripts

rutas["GPT"]="$BASE_DIR/ebo_gpt"
scripts["GPT"]="ebo_gpt.py"

rutas["Pasapalabra"]="$BASE_DIR/pasapalabra"
scripts["Pasapalabra"]="pasapalabra.py"

rutas["SimonSay"]="$BASE_DIR/simonSay"
scripts["SimonSay"]="simonSay.py"

rutas["Storytelling"]="$BASE_DIR/storytelling"
scripts["Storytelling"]="storytelling.py"

rutas["APP_JUEGOS"]="$BASE_DIR/app_juegos"
scripts["APP_JUEGOS"]="app_juegos.py"

rutas["EBO_APP"]="$BASE_DIR/ebo_app"
scripts["EBO_APP"]="ebo_app.py"

rutas["therapistPanel"]="$BASE_DIR/therapistPanel"
scripts["therapistPanel"]="therapistPanel.py"

# Función para abrir una pestaña en gnome-terminal con entorno virtual
function abrir_pestana {
    if [ "$2" == "therapistPanel" ]; then
        # CASO 1: Es el Panel del Terapeuta (carpeta generated + venv)
        gnome-terminal --tab -- bash -c "
            cd '$1' &&
            echo 'Activando games_venv...' &&
            source '$BASE_DIR/games_venv/bin/activate' &&
            echo 'Iniciando Therapist Panel en generated...' &&
            python3 generated/$3 etc/config;
            exec bash
        "
    else      
        # CASO 2: Resto de componentes (carpeta src + venv)
        gnome-terminal --tab -- bash -c "
            cd '$1' &&
            echo 'Activando games_venv...' &&
            source '$BASE_DIR/games_venv/bin/activate' &&
            echo 'Ejecutando en $2' &&
            python3 src/$3 etc/config;
            exec bash
        "
    fi
}

# Iterar sobre las rutas y abrir pestañas
for nombre in "${!rutas[@]}"; do
    abrir_pestana "${rutas[$nombre]}" "$nombre" "${scripts[$nombre]}"
done

