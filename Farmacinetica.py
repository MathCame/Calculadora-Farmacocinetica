import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk

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
    # Intervalos de dosificación base en horas
    intervalos_base = {
        "Ibuprofeno": 6,
        "Paracetamol": 6,
        "Aspirina": 6,
        "Amoxicilina": 8,
        "Metformina": 12,
        "Loratadina": 24
    }
    
    # Obtener el intervalo base
    intervalo = intervalos_base.get(medicamento, 8)  # Valor por defecto 8 horas

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

# Función para ejecutar la simulación y mostrar las órbitas periódicas
def ejecutar_simulacion():
    # Obtener los valores ingresados
    try:
        masa = float(entry_masa.get())
        altura = float(entry_altura.get())
        edad = int(entry_edad.get())
    except ValueError:
        label_intervalo.config(text="Por favor, ingrese valores numéricos válidos.")
        return

    genero = genero_var.get()
    comorbilidad = comorbilidad_var.get()
    genetica = genetica_var.get()
    alergia = alergia_var.get()
    medicamento = medicamento_var.get()

    # Calcular el IMC
    imc = masa / (altura ** 2)

    # Mapear factores de genética y alergia a valores numéricos si es necesario
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

    # Definir los parámetros del paciente
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

    # Condiciones iniciales
    y0 = [0, 100, params['V_d']]

    # Tiempo de simulación (24 horas con más puntos para una animación suave)
    t = np.linspace(0, 24, 500)

    # Resolver las ecuaciones diferenciales
    sol = odeint(ecuaciones, y0, t, args=(params, medicamento))

    # Calcular el intervalo de dosificación
    intervalo_dosificacion = calcular_intervalo_dosificacion(params, medicamento)

    # Mostrar el intervalo de dosificación
    label_intervalo.config(text=f"Intervalo de dosificación recomendado: cada {intervalo_dosificacion:.1f} horas")

    # Crear una nueva ventana para los gráficos
    graph_window = tk.Toplevel(root)
    graph_window.title(f"Resultados Farmacocinéticos - {medicamento}")
    graph_window.geometry("1200x700")

    # Crear figura para los gráficos
    fig = plt.figure(figsize=(12, 6), dpi=100)
    fig.suptitle(f"Simulación Farmacocinética - {medicamento}", fontsize=14)

    # Gráfico 1: Evolución temporal
    ax1 = fig.add_subplot(1, 2, 1)
    line1, = ax1.plot([], [], 'b-', label='Concentración plasmática (C)')
    line2, = ax1.plot([], [], 'r-', label='Cantidad en tracto digestivo (D)')
    line3, = ax1.plot([], [], 'g-', label='Volumen de distribución (V)')
    ax1.set_xlim(0, 24)
    ax1.set_ylim(0, max(np.max(sol[:,0]), np.max(sol[:,1]), np.max(sol[:,2])) * 1.1)
    ax1.set_xlabel('Tiempo (horas)')
    ax1.set_ylabel('Concentración / Cantidad')
    ax1.set_title('Evolución Temporal')
    ax1.legend()
    ax1.grid(True)

    # Gráfico 2: Órbitas periódicas
    ax2 = fig.add_subplot(1, 2, 2)
    orbit_line, = ax2.plot([], [], 'b-', alpha=0.5)
    current_point, = ax2.plot([], [], 'ro')
    ax2.set_xlim(np.min(sol[:,0]) * 1.1, np.max(sol[:,0]) * 1.1)
    ax2.set_ylim(np.min(sol[:,2]) * 1.1, np.max(sol[:,2]) * 1.1)
    ax2.set_xlabel('Concentración plasmática (C)')
    ax2.set_ylabel('Volumen de distribución (V)')
    ax2.set_title('Órbitas Periódicas en el Espacio de Fases')
    ax2.grid(True)

    # Añadir la figura a la ventana de Tkinter
    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Función de inicialización para la animación
    def init():
        line1.set_data([], [])
        line2.set_data([], [])
        line3.set_data([], [])
        orbit_line.set_data([], [])
        current_point.set_data([], [])
        return line1, line2, line3, orbit_line, current_point

    # Función de animación
    def animate(i):
        # Actualizar gráfico temporal
        line1.set_data(t[:i], sol[:i, 0])
        line2.set_data(t[:i], sol[:i, 1])
        line3.set_data(t[:i], sol[:i, 2])
        
        # Actualizar gráfico de órbitas
        orbit_line.set_data(sol[:i, 0], sol[:i, 2])
        current_point.set_data(sol[i, 0], sol[i, 2])
        
        return line1, line2, line3, orbit_line, current_point

    # Crear la animación
    ani = FuncAnimation(fig, animate, frames=len(t), init_func=init,
                        blit=True, interval=50, repeat=True)

    # Añadir botón para guardar la animación
    def guardar_animacion():
        from matplotlib.animation import PillowWriter
        writer = PillowWriter(fps=15)
        ani.save("farmacocinetica.gif", writer=writer)
        tk.messagebox.showinfo("Guardado", "Animación guardada como farmacocinetica.gif")

    btn_guardar = ttk.Button(graph_window, text="Guardar Animación", command=guardar_animacion)
    btn_guardar.pack(side=tk.BOTTOM, pady=10)

# Crear la ventana principal de la interfaz
root = tk.Tk()
root.title("Calculadora Farmacocinética Avanzada")
root.geometry("600x650")

# Estilos mejorados
style = ttk.Style()
style.theme_use('clam')
style.configure('TFrame', background='#f0f8ff')
style.configure('TLabel', background='#f0f8ff', font=('Arial', 11))
style.configure('TButton', font=('Arial', 11, 'bold'), background='#4b8bbe', foreground='white')
style.configure('TEntry', font=('Arial', 11))
style.configure('TOptionMenu', font=('Arial', 11))
style.map('TButton', background=[('active', '#3a7ab1')])

main_frame = ttk.Frame(root, padding="15 15 15 15")
main_frame.pack(fill=tk.BOTH, expand=True)

# Variables para los campos de entrada
medicamento_var = tk.StringVar(value="Ibuprofeno")
genero_var = tk.StringVar(value="Hombre")
comorbilidad_var = tk.StringVar(value="Sin comorbilidad")
genetica_var = tk.StringVar(value="Metabolizador normal")
alergia_var = tk.StringVar(value="Sin alergia")

# Listas de opciones
lista_medicamentos = ["Ibuprofeno", "Paracetamol", "Aspirina", "Amoxicilina", "Metformina", "Loratadina"]
lista_genero = ["Hombre", "Mujer"]
lista_comorbilidades = ["Sin comorbilidad", "Diabetes", "Insuficiencia renal", "Insuficiencia hepática", "Hipertensión", "Asma"]
lista_genetica = ["Metabolizador normal", "Metabolizador rápido", "Metabolizador lento", "No identificado"]
lista_alergia = ["Sin alergia", "Alergia leve", "Alergia moderada", "Alergia severa"]

# Crear y colocar widgets de la interfaz
ttk.Label(main_frame, text="Datos del Paciente", font=('Arial', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=10, sticky='w')

row = 1
ttk.Label(main_frame, text="Masa (kg):").grid(row=row, column=0, sticky='e', pady=5)
entry_masa = ttk.Entry(main_frame, width=15)
entry_masa.grid(row=row, column=1, pady=5, sticky='w')
row += 1

ttk.Label(main_frame, text="Altura (m):").grid(row=row, column=0, sticky='e', pady=5)
entry_altura = ttk.Entry(main_frame, width=15)
entry_altura.grid(row=row, column=1, pady=5, sticky='w')
row += 1

ttk.Label(main_frame, text="Edad (años):").grid(row=row, column=0, sticky='e', pady=5)
entry_edad = ttk.Entry(main_frame, width=15)
entry_edad.grid(row=row, column=1, pady=5, sticky='w')
row += 1

ttk.Label(main_frame, text="Género:").grid(row=row, column=0, sticky='e', pady=5)
genero_menu = ttk.OptionMenu(main_frame, genero_var, lista_genero[0], *lista_genero)
genero_menu.grid(row=row, column=1, pady=5, sticky='w')
row += 1

ttk.Label(main_frame, text="Comorbilidad:").grid(row=row, column=0, sticky='e', pady=5)
comorbilidad_menu = ttk.OptionMenu(main_frame, comorbilidad_var, lista_comorbilidades[0], *lista_comorbilidades)
comorbilidad_menu.grid(row=row, column=1, pady=5, sticky='w')
row += 1

ttk.Label(main_frame, text="Genética:").grid(row=row, column=0, sticky='e', pady=5)
genetica_menu = ttk.OptionMenu(main_frame, genetica_var, lista_genetica[0], *lista_genetica)
genetica_menu.grid(row=row, column=1, pady=5, sticky='w')
row += 1

ttk.Label(main_frame, text="Alergia:").grid(row=row, column=0, sticky='e', pady=5)
alergia_menu = ttk.OptionMenu(main_frame, alergia_var, lista_alergia[0], *lista_alergia)
alergia_menu.grid(row=row, column=1, pady=5, sticky='w')
row += 1

ttk.Label(main_frame, text="Medicamento:", font=('Arial', 11, 'bold')).grid(row=row, column=0, sticky='e', pady=10)
medicamento_menu = ttk.OptionMenu(main_frame, medicamento_var, lista_medicamentos[0], *lista_medicamentos)
medicamento_menu.grid(row=row, column=1, pady=10, sticky='w')
row += 1

# Botón para ejecutar la simulación
btn_simular = ttk.Button(main_frame, text="Ejecutar Simulación", command=ejecutar_simulacion)
btn_simular.grid(row=row, column=0, columnspan=2, pady=20)
row += 1

# Etiqueta para mostrar el intervalo de dosificación
label_intervalo = ttk.Label(main_frame, text="", foreground='blue', font=('Arial', 12, 'bold'))
label_intervalo.grid(row=row, column=0, columnspan=2, pady=10)

# Establecer valores por defecto
entry_masa.insert(0, "70")
entry_altura.insert(0, "1.75")
entry_edad.insert(0, "30")

# Iniciar la aplicación
root.mainloop()
