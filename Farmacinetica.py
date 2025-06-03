import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import tkinter as tk
from tkinter import ttk, messagebox
import matplotlib.animation as animation

# Funciones farmacocinéticas
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

def ecuaciones(y, t, params, medicamento):
    C, D, V = y
    f = funcion_f(C, t, D, V, params, medicamento)
    g = funcion_g(D, t, params, medicamento)
    
    k_e = params['k_e']
    
    if params['comorbilidad'] == "Insuficiencia renal":
        if medicamento in ["Metformina", "Amoxicilina"]:
            k_e *= 0.5
    
    if params['comorbilidad'] == "Insuficiencia hepática":
        if medicamento in ["Paracetamol", "Ibuprofeno"]:
            k_e *= 0.7
    
    dC_dt = f - k_e * C
    dD_dt = -params['k_a'] * g
    dV_dt = params['k_a'] * D - k_e * V
    return [dC_dt, dD_dt, dV_dt]

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

    if params['comorbilidad'] == "Insuficiencia renal":
        if medicamento in ["Metformina", "Amoxicilina"]:
            intervalo *= 1.5

    if params['comorbilidad'] == "Insuficiencia hepática":
        if medicamento in ["Paracetamol", "Ibuprofeno"]:
            intervalo *= 1.3

    if params['genetica'] == "Metabolizador rápido":
        intervalo *= 0.9
    elif params['genetica'] == "Metabolizador lento":
        intervalo *= 1.1

    if params['masa'] > 90:
        intervalo *= 0.95
    elif params['masa'] < 50:
        intervalo *= 1.05

    if medicamento == "Loratadina":
        if params['alergia'] == "Alergia leve":
            intervalo *= 1.1
        elif params['alergia'] == "Alergia moderada":
            intervalo *= 1.2
        elif params['alergia'] == "Alergia severa":
            intervalo *= 1.3

    intervalo = max(4, min(intervalo, 48))  # Extendí el máximo a 48 horas
    
    return intervalo

def ejecutar_simulacion():
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

    imc = masa / (altura ** 2)

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

    y0 = [0, 100, params['V_d']]
    t = np.linspace(0, 24, 500)
    sol = odeint(ecuaciones, y0, t, args=(params, medicamento))

    intervalo_dosificacion = calcular_intervalo_dosificacion(params, medicamento)
    label_intervalo.config(text=f"Intervalo de dosificación recomendado: cada {intervalo_dosificacion:.1f} horas")

    graph_window = tk.Toplevel(root)
    graph_window.title(f"Resultados - {medicamento}")
    graph_window.geometry("1200x700")

    fig = plt.figure(figsize=(12, 6), dpi=100)
    fig.suptitle(f"Simulación Farmacocinética - {medicamento}", fontsize=14)

    ax1 = fig.add_subplot(1, 2, 1)
    line1, = ax1.plot([], [], 'b-', label='Concentración (C)')
    line2, = ax1.plot([], [], 'r-', label='Tracto digestivo (D)')
    line3, = ax1.plot([], [], 'g-', label='Volumen (V)')
    ax1.set_xlim(0, 24)
    ax1.set_ylim(0, max(np.max(sol[:,0]), np.max(sol[:,1]), np.max(sol[:,2])) * 1.1)
    ax1.set_xlabel('Tiempo (horas)')
    ax1.set_ylabel('Concentración / Cantidad')
    ax1.set_title('Evolución Temporal (Dosis Única)')
    ax1.legend()
    ax1.grid(True)

    ax2 = fig.add_subplot(1, 2, 2)
    orbit_line, = ax2.plot([], [], 'b-', alpha=0.7)
    current_point, = ax2.plot([], [], 'ro')
    ax2.set_xlim(np.min(sol[:,0]) * 1.1, np.max(sol[:,0]) * 1.1)
    ax2.set_ylim(np.min(sol[:,2]) * 1.1, np.max(sol[:,2]) * 1.1)
    ax2.set_xlabel('Concentración (C)')
    ax2.set_ylabel('Volumen (V)')
    ax2.set_title('Trayectoria en Espacio de Fases')
    ax2.grid(True)

    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def init():
        line1.set_data([], [])
        line2.set_data([], [])
        line3.set_data([], [])
        orbit_line.set_data([], [])
        current_point.set_data([], [])
        return line1, line2, line3, orbit_line, current_point

    def animate(i):
        line1.set_data(t[:i], sol[:i, 0])
        line2.set_data(t[:i], sol[:i, 1])
        line3.set_data(t[:i], sol[:i, 2])
        orbit_line.set_data(sol[:i, 0], sol[:i, 2])
        current_point.set_data(sol[i, 0], sol[i, 2])
        return line1, line2, line3, orbit_line, current_point

    ani = FuncAnimation(fig, animate, frames=len(t), init_func=init,
                        blit=True, interval=20, repeat=True)

    def guardar_animacion():
        try:
            writer = animation.PillowWriter(fps=20)
            ani.save("farmacocinetica.gif", writer=writer)
            messagebox.showinfo("Guardado", "Animación guardada como farmacocinetica.gif")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")

    btn_guardar = ttk.Button(graph_window, text="Guardar Animación", command=guardar_animacion)
    btn_guardar.pack(side=tk.BOTTOM, pady=10)

def ejecutar_simulacion_periodica():
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

    imc = masa / (altura ** 2)

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

    intervalo = calcular_intervalo_dosificacion(params, medicamento)
    num_dosis = 5
    puntos_por_ciclo = 150
    
    t_total = 0
    t_segmentos = []
    sol_segmentos = []
    y0 = [0, 100, params['V_d']]
    
    for ciclo in range(num_dosis):
        t_segmento = np.linspace(t_total, t_total + intervalo, puntos_por_ciclo)
        sol_segmento = odeint(ecuaciones, y0, t_segmento, args=(params, medicamento))
        
        t_segmentos.append(t_segmento)
        sol_segmentos.append(sol_segmento)
        
        y0 = sol_segmento[-1, :].copy()
        y0[1] += 100
        t_total += intervalo
    
    t = np.concatenate(t_segmentos)
    sol = np.concatenate(sol_segmentos, axis=0)
    
    graph_window = tk.Toplevel(root)
    graph_window.title(f"Simulación Periódica - {medicamento}")
    graph_window.geometry("1300x750")

    fig = plt.figure(figsize=(13, 6), dpi=100)
    fig.suptitle(f"Dosis Múltiples - {medicamento} (Cada {intervalo:.1f} horas)", fontsize=14)

    ax1 = fig.add_subplot(1, 2, 1)
    colors = plt.cm.viridis(np.linspace(0, 1, num_dosis))
    for i in range(num_dosis):
        start = i * puntos_por_ciclo
        end = (i+1) * puntos_por_ciclo
        ax1.plot(t[start:end], sol[start:end, 0], color=colors[i], 
                label=f'Dosis {i+1}' if i < 5 else None)
    
    for i in range(num_dosis):
        ax1.axvline(x=i*intervalo, color='r', linestyle='--', alpha=0.3)
    
    ax1.set_xlim(0, t[-1])
    ax1.set_ylim(0, np.max(sol[:,0]) * 1.1)
    ax1.set_xlabel('Tiempo (horas)')
    ax1.set_ylabel('Concentración (C)')
    ax1.set_title('Evolución con Dosis Múltiples')
    ax1.legend()
    ax1.grid(True)

    ax2 = fig.add_subplot(1, 2, 2)
    points = np.array([sol[:,0], sol[:,2]]).T.reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    
    norm = plt.Normalize(0, t[-1])
    cmap = plt.cm.plasma
    
    lc = LineCollection(segments, cmap=cmap, norm=norm, alpha=0.8)
    lc.set_array(t)
    lc.set_linewidth(2)
    line = ax2.add_collection(lc)
    
    current_point, = ax2.plot([], [], 'ro', markersize=8)
    
    ax2.set_xlim(np.min(sol[:,0]) * 0.9, np.max(sol[:,0]) * 1.1)
    ax2.set_ylim(np.min(sol[:,2]) * 0.9, np.max(sol[:,2]) * 1.1)
    ax2.set_xlabel('Concentración (C)')
    ax2.set_ylabel('Volumen (V)')
    ax2.set_title('Órbitas Periódicas (Evolución Temporal)')
    ax2.grid(True)
    
    cbar = fig.colorbar(lc, ax=ax2)
    cbar.set_label('Tiempo (horas)')

    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def animate(i):
        current_point.set_data(sol[i, 0], sol[i, 2])
        lc.set_segments(segments[:i])
        lc.set_array(t[:i])
        return lc, current_point

    ani = FuncAnimation(fig, animate, frames=len(t), interval=20, blit=True)

    def guardar_animacion():
        try:
            writer = animation.PillowWriter(fps=20)
            ani.save("orbita_periodica.gif", writer=writer)
            messagebox.showinfo("Guardado", "Animación guardada como orbita_periodica.gif")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")

    btn_guardar = ttk.Button(graph_window, text="Guardar Animación", command=guardar_animacion)
    btn_guardar.pack(side=tk.BOTTOM, pady=10)

# Interfaz gráfica
root = tk.Tk()
root.title("Simulador Farmacocinético Avanzado")
root.geometry("650x750")

style = ttk.Style()
style.theme_use('clam')
style.configure('TFrame', background='#f0f8ff')
style.configure('TLabel', background='#f0f8ff', font=('Arial', 11))
style.configure('TButton', font=('Arial', 11, 'bold'), background='#4b8bbe', foreground='white')
style.configure('TEntry', font=('Arial', 11))
style.configure('TOptionMenu', font=('Arial', 11))
style.map('TButton', background=[('active', '#3a7ab1')])

main_frame = ttk.Frame(root, padding="20 20 20 20")
main_frame.pack(fill=tk.BOTH, expand=True)

medicamento_var = tk.StringVar(value="Ibuprofeno")
genero_var = tk.StringVar(value="Hombre")
comorbilidad_var = tk.StringVar(value="Sin comorbilidad")
genetica_var = tk.StringVar(value="Metabolizador normal")
alergia_var = tk.StringVar(value="Sin alergia")

lista_medicamentos = ["Ibuprofeno", "Paracetamol", "Aspirina", "Amoxicilina", "Metformina", "Loratadina"]
lista_genero = ["Hombre", "Mujer"]
lista_comorbilidades = ["Sin comorbilidad", "Diabetes", "Insuficiencia renal", "Insuficiencia hepática", "Hipertensión", "Asma"]
lista_genetica = ["Metabolizador normal", "Metabolizador rápido", "Metabolizador lento", "No identificado"]
lista_alergia = ["Sin alergia", "Alergia leve", "Alergia moderada", "Alergia severa"]

ttk.Label(main_frame, text="Datos del Paciente", font=('Arial', 14, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0,15))

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

btn_simular = ttk.Button(main_frame, text="Simulación Básica (Dosis Única)", command=ejecutar_simulacion)
btn_simular.grid(row=row, column=0, columnspan=2, pady=(15,5))
row += 1

btn_periodico = ttk.Button(main_frame, text="Simulación Avanzada (Dosis Múltiples)", command=ejecutar_simulacion_periodica)
btn_periodico.grid(row=row, column=0, columnspan=2, pady=(5,15))
row += 1

label_intervalo = ttk.Label(main_frame, text="", foreground='blue', font=('Arial', 12, 'bold'))
label_intervalo.grid(row=row, column=0, columnspan=2, pady=(10,0))
row += 1

ttk.Label(main_frame, text="Instrucciones:", font=('Arial', 11, 'bold')).grid(row=row, column=0, sticky='w', pady=(20,5))
row += 1
ttk.Label(main_frame, text="1. Complete los datos del paciente\n2. Seleccione el medicamento\n3. Elija el tipo de simulación", 
          justify=tk.LEFT).grid(row=row, column=0, columnspan=2, sticky='w')

entry_masa.insert(0, "70")
entry_altura.insert(0, "1.75")
entry_edad.insert(0, "30")

root.mainloop()
