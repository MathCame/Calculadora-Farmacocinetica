import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
import concurrent.futures
import colorsys
import tkinter as tk
from tkinter import ttk
import matplotlib
matplotlib.use('TkAgg')  # Forzar el uso del backend Tkinter para asegurar visualización

# Funciones f y g dependientes del medicamento y parámetros del paciente
def funcion_f(C, t, D, V, params, medicamento):
    if medicamento == "Ibuprofeno":
        return (params['k_a'] * D / V) * (1 / (1 + 0.1 * params['masa'] / 70 + 0.1 * (1 if params['genero'] == "Hombre" else 0)))
    elif medicamento == "Paracetamol":
        return params['k_a'] * D ** 0.75 / V
    elif medicamento == "Aspirina":
        return params['k_a'] * (D / V) * np.exp(-0.05 * t)
    elif medicamento == "Amoxicilina":
        return params['k_a'] * D / V * (1 + 0.02 * params['edad'])
    elif medicamento == "Metformina":
        return params['k_a'] * D / V
    elif medicamento == "Loratadina":
        return params['k_a'] * D / V * np.exp(-0.03 * t)
    else:
        return 0

def funcion_g(D, t, params, medicamento):
    if medicamento == "Ibuprofeno":
        return D / (t + 1) * (1 + 0.05 * params['edad'] / 50)
    elif medicamento == "Paracetamol":
        return np.log(D + 1) * (1 + 0.1 * params['genetica_factor'])
    elif medicamento == "Aspirina":
        return np.sqrt(D)
    elif medicamento == "Amoxicilina":
        return D / (params['V_d'] * (1 + 0.1 * params['genetica_factor']))
    elif medicamento == "Metformina":
        return D * np.exp(-params['k_e'] * t)
    elif medicamento == "Loratadina":
        return D / (t + 1) * (1 + 0.05 * params['alergia_factor'])
    else:
        return 0

# Ecuaciones diferenciales
def ecuaciones(y, t, params, medicamento):
    C, D, V = y
    f = funcion_f(C, t, D, V, params, medicamento)
    g = funcion_g(D, t, params, medicamento)
    
    # Ajuste de k_e según comorbilidades específicas
    k_e = params['k_e']
    
    # Insuficiencia renal afecta a Metformina y Amoxicilina
    if params['comorbilidad'] == "Insuficiencia renal":
        if medicamento in ["Metformina", "Amoxicilina"]:
            k_e *= 0.5  # Disminuir k_e en un 50%
    
    # Insuficiencia hepática afecta a Paracetamol e Ibuprofeno
    if params['comorbilidad'] == "Insuficiencia hepática":
        if medicamento in ["Paracetamol", "Ibuprofeno"]:
            k_e *= 0.7  # Disminuir k_e en un 30%
    
    dC_dt = f - k_e * C
    dD_dt = -params['k_a'] * g
    dV_dt = params['k_a'] * D - k_e * V
    return [dC_dt, dD_dt, dV_dt]

# Función para calcular el intervalo de dosificación ajustado
def calcular_intervalo_dosificacion(params, medicamento):
    intervalos_base = {
        "Ibuprofeno": 6,
        "Paracetamol": 6,
        "Aspirina": 6,
        "Amoxicilina": 8,
        "Metformina": 12,
        "Loratadina": 24
    }
    intervalo = intervalos_base.get(medicamento, 8)

    # Ajustes por comorbilidad específica
    if params['comorbilidad'] == "Insuficiencia renal":
        if medicamento in ["Metformina", "Amoxicilina"]:
            intervalo *= 1.5  # Aumentar el intervalo en un 50%

    if params['comorbilidad'] == "Insuficiencia hepática":
        if medicamento in ["Paracetamol", "Ibuprofeno"]:
            intervalo *= 1.3  # Aumentar el intervalo en un 30%

    # Ajustes por genética (metabolismo)
    if params['genetica'] == "Metabolizador rápido":
        intervalo *= 0.9  # Reducir el intervalo en un 10%
    elif params['genetica'] == "Metabolizador lento":
        intervalo *= 1.1  # Aumentar el intervalo en un 10%

    # Ajustes por masa corporal
    if params['masa'] > 90:
        intervalo *= 0.95  # Reducir intervalo en un 5%
    elif params['masa'] < 50:
        intervalo *= 1.05  # Aumentar intervalo en un 5%

    # Ajustes por alergias (para Loratadina)
    if medicamento == "Loratadina":
        if params['alergia'] == "Alergia leve":
            intervalo *= 1.1
        elif params['alergia'] == "Alergia moderada":
            intervalo *= 1.2
        elif params['alergia'] == "Alergia severa":
            intervalo *= 1.3

    # Limitar el intervalo entre 4 y 24 horas
    intervalo = max(4, min(intervalo, 24))

    return intervalo

# Función para generar colores distintos
def generar_colores(n):
    colores = []
    for i in range(n):
        hue = i / n  # Variar el tono de 0 a 1
        saturation = 0.9  # Saturación alta
        value = 0.9  # Valor alto
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        colores.append((r, g, b))
    return colores

# Función para ejecutar las simulaciones
def ejecutar_simulaciones():
    num_simulaciones = 100
    medicamentos = [medicamento_var.get()]
    resultados = {}
    
    # Generar condiciones aleatorias de pacientes
    np.random.seed(42)  # Fijar semilla para reproducibilidad
    condiciones_pacientes = []
    for _ in range(num_simulaciones):
        masa = np.random.uniform(50, 100)
        altura = np.random.uniform(1.5, 2.0)
        edad = np.random.randint(18, 80)
        genero = np.random.choice(["Hombre", "Mujer"])
        comorbilidad = np.random.choice(lista_comorbilidades)
        genetica = np.random.choice(lista_genetica)
        alergia = np.random.choice(lista_alergia)
        condicion = {
            'masa': masa,
            'altura': altura,
            'edad': edad,
            'genero': genero,
            'comorbilidad': comorbilidad,
            'genetica': genetica,
            'alergia': alergia
        }
        condiciones_pacientes.append(condicion)
    
    # Ejecutar simulaciones en paralelo
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futuros = []
        for medicamento in medicamentos:
            futuros.append(executor.submit(simular_medicamento_condiciones, medicamento, condiciones_pacientes))
        for futuro in concurrent.futures.as_completed(futuros):
            med, res = futuro.result()
            resultados[med] = res
    return resultados

def simular_medicamento_condiciones(medicamento, condiciones_pacientes):
    resultados = []
    for idx, condicion in enumerate(condiciones_pacientes, 1):
        masa = condicion['masa']
        altura = condicion['altura']
        imc = masa / (altura ** 2)
        edad = condicion['edad']
        genero = condicion['genero']
        comorbilidad = condicion['comorbilidad']
        genetica = condicion['genetica']
        alergia = condicion['alergia']
        
        genetica_factor = 0.0
        if genetica == "Metabolizador rápido":
            genetica_factor = 0.2
        elif genetica == "Metabolizador lento":
            genetica_factor = -0.2

        alergia_factor = 0.0
        if alergia == "Alergia leve":
            alergia_factor = 0.1
        elif alergia == "Alergia moderada":
            alergia_factor = 0.2
        elif alergia == "Alergia severa":
            alergia_factor = 0.3

        params = {
            'masa': masa,
            'altura': altura,
            'imc': imc,
            'edad': edad,
            'genero': genero,
            'comorbilidad': comorbilidad,
            'genetica': genetica,
            'genetica_factor': genetica_factor,
            'alergia': alergia,
            'alergia_factor': alergia_factor,
            'V_d': 0.6 * masa,
            'k_a': 0.5 * (1 + 0.01 * imc),
            'k_e': 0.3 * (1 - 0.01 * imc)
        }

        intervalo_dosificacion = calcular_intervalo_dosificacion(params, medicamento)
        y0 = [0, 100, params['V_d']]

        t = np.linspace(0, 24, 1000)
        sol = odeint(ecuaciones, y0, t, args=(params, medicamento))

        resultados.append((t, sol, params, idx, intervalo_dosificacion))
    return medicamento, resultados

# Función para ejecutar la simulación y mostrar las órbitas periódicas
def ejecutar_simulacion():
    resultados = ejecutar_simulaciones()
    medicamento = medicamento_var.get()
    res_medicamento = resultados[medicamento]

    num_simulaciones = len(res_medicamento)
    colores = generar_colores(num_simulaciones)

    for idx, ((t, sol, params, sim_idx, intervalo_dosificacion), color) in enumerate(zip(res_medicamento, colores), 1):
        color_hex = '#%02x%02x%02x' % tuple((np.array(color) * 255).astype(int))
        descripcion = f"Simulación {idx}:\n"
        descripcion += f"  Masa: {params['masa']:.2f} kg\n"
        descripcion += f"  Altura: {params['altura']:.2f} m\n"
        descripcion += f"  Edad: {params['edad']} años\n"
        descripcion += f"  Género: {params['genero']}\n"
        descripcion += f"  Comorbilidad: {params['comorbilidad']}\n"
        descripcion += f"  Genética: {params['genetica']}\n"
        descripcion += f"  Alergia: {params['alergia']}\n"
        descripcion += f"  Intervalo de dosificación: {intervalo_dosificacion:.2f} horas\n"
        descripcion += f"  Color asignado: {color_hex}\n"
        print(descripcion)

    plt.figure(figsize=(12, 6))
    for (t, sol, params, sim_idx, intervalo_dosificacion), color in zip(res_medicamento, colores):
        C = sol[:, 0]
        V = sol[:, 2]
        plt.plot(C, V, color=color)

    plt.xlabel('Concentración plasmática (C)')
    plt.ylabel('Volumen de distribución (V)')
    plt.title(f'Órbitas Periódicas - {medicamento}')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

# Crear la ventana principal de la interfaz
root = tk.Tk()
root.title("Simulación Farmacocinética de 100 Pacientes")

# Estilos
style = ttk.Style()
style.configure('TFrame', background='#f0f0f0')
style.configure('TLabel', background='#f0f0f0', font=('Arial', 12))
style.configure('TButton', font=('Arial', 12))
style.configure('TOptionMenu', font=('Arial', 12))

main_frame = ttk.Frame(root, padding="10 10 10 10")
main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

# Variables para los campos de entrada
medicamento_var = tk.StringVar(value="Ibuprofeno")

# Lista de medicamentos
lista_medicamentos = ["Ibuprofeno", "Paracetamol", "Aspirina", "Amoxicilina", "Metformina", "Loratadina"]
lista_genero = ["Hombre", "Mujer"]
lista_comorbilidades = ["Sin comorbilidad", "Diabetes", "Insuficiencia renal", "Insuficiencia hepática", "Hipertensión", "Asma"]
lista_genetica = ["Metabolizador normal", "Metabolizador rápido", "Metabolizador lento", "No identificado"]
lista_alergia = ["Sin alergia", "Alergia leve", "Alergia moderada", "Alergia severa"]

# Crear y colocar widgets de la interfaz
row = 0

ttk.Label(main_frame, text="Medicamento a Simular:").grid(row=row, column=0, sticky='e', pady=5)
medicamento_menu = ttk.OptionMenu(main_frame, medicamento_var, lista_medicamentos[0], *lista_medicamentos)
medicamento_menu.grid(row=row, column=1, pady=5, sticky='w')
row += 1

# Botón para ejecutar la simulación
ttk.Button(main_frame, text="Ejecutar Simulación", command=ejecutar_simulacion).grid(row=row, column=0, columnspan=2, pady=15)
row += 1

# Ajustar el tamaño de las columnas
main_frame.columnconfigure(0, weight=1)
main_frame.columnconfigure(1, weight=2)

# Iniciar la aplicación
root.mainloop()
