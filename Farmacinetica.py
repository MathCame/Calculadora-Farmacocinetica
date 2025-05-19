import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import tkinter as tk
from tkinter import ttk, messagebox

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
    
    # Ajuste de k_e según comorbilidades
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

# Función para calcular el intervalo de dosificación
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

    intervalo = max(4, min(intervalo, 48))  # Límite extendido a 48 horas
    return intervalo

# Función principal de simulación
def ejecutar_simulacion():
    try:
        masa = float(entry_masa.get())
        altura = float(entry_altura.get())
        edad = int(entry_edad.get())
    except ValueError:
        label_intervalo.config(text="Error: Ingrese valores numéricos válidos.")
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

    # Simulación con múltiples dosis
    intervalo = calcular_intervalo_dosificacion(params, medicamento)
    num_dosis = 5  # Número total de dosis
    puntos_por_dosis = 100  # Resolución temporal

    t_total = 0
    t_segmentos = []
    sol_segmentos = []
    y0 = [0, 100, params['V_d']]  # Primera dosis

    for _ in range(num_dosis):
        t_segmento = np.linspace(t_total, t_total + intervalo, puntos_por_dosis)
        sol_segmento = odeint(ecuaciones, y0, t_segmento, args=(params, medicamento))
        
        t_segmentos.append(t_segmento)
        sol_segmentos.append(sol_segmento)
        
        # Preparar siguiente dosis
        y0 = sol_segmento[-1, :]
        y0[1] += 100  # Nueva dosis (100 mg)
        
        t_total += intervalo

    # Concatenar resultados
    t = np.concatenate(t_segmentos)
    sol = np.concatenate(sol_segmentos, axis=0)

    # Mostrar intervalo de dosificación
    label_intervalo.config(text=f"Intervalo de dosificación: {intervalo:.1f} horas")

    # Crear ventana de gráficos 3D
    graph_window = tk.Toplevel(root)
    graph_window.title(f"Farmacocinética 3D - {medicamento}")
    graph_window.geometry("1200x800")

    fig = plt.figure(figsize=(12, 8), dpi=100)
    ax3d = fig.add_subplot(111, projection='3d')
    
    ax3d.set_xlabel('Concentración (C)')
    ax3d.set_ylabel('Volumen (V)')
    ax3d.set_zlabel('Tiempo (horas)')
    ax3d.set_title(f'Órbita Farmacocinética 3D - {medicamento}')
    
    ax3d.set_xlim(np.min(sol[:,0]), np.max(sol[:,0])*1.1)
    ax3d.set_ylim(np.min(sol[:,2]), np.max(sol[:,2])*1.1)
    ax3d.set_zlim(0, t[-1])

    # Línea 3D y punto actual
    line3d, = ax3d.plot([], [], [], 'b-', alpha=0.7, linewidth=2)
    current_point, = ax3d.plot([], [], [], 'ro', markersize=8)
    
    # Marcadores de dosis (estrellas verdes)
    for i in range(num_dosis):
        ax3d.plot([0], [0], [i*intervalo], 'g*', markersize=10, label=f"Dosis {i+1}" if i == 0 else "")

    # Leyenda
    ax3d.legend()

    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    # Animación
    def init():
        line3d.set_data([], [])
        line3d.set_3d_properties([])
        current_point.set_data([], [])
        current_point.set_3d_properties([])
        return line3d, current_point

    def animate(i):
        line3d.set_data(sol[:i,0], sol[:i,2])
        line3d.set_3d_properties(t[:i])
        
        current_point.set_data([sol[i,0]], [sol[i,2]])
        current_point.set_3d_properties([t[i]])
        
        # Rotación suave
        ax3d.view_init(elev=20, azim=i/10 % 360)
        
        return line3d, current_point

    ani = FuncAnimation(fig, animate, frames=len(t), init_func=init,
                        blit=True, interval=50, repeat=True)

    # Botón para guardar animación
    def guardar_animacion():
        try:
            from matplotlib.animation import PillowWriter
            writer = PillowWriter(fps=20)
            ani.save("farmacocinetica_3d.gif", writer=writer)
            messagebox.showinfo("Guardado", "Animación guardada como farmacocinetica_3d.gif")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo guardar: {str(e)}")

    btn_guardar = ttk.Button(graph_window, text="Guardar Animación", command=guardar_animacion)
    btn_guardar.pack(side=tk.BOTTOM, pady=10)

# Interfaz gráfica
root = tk.Tk()
root.title("Simulación Farmacocinética 3D")
root.geometry("600x700")

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

# Variables de la interfaz
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

# Widgets de la interfaz
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

btn_simular = ttk.Button(main_frame, text="Simular en 3D", command=ejecutar_simulacion)
btn_simular.grid(row=row, column=0, columnspan=2, pady=20)
row += 1

label_intervalo = ttk.Label(main_frame, text="", foreground='blue', font=('Arial', 12, 'bold'))
label_intervalo.grid(row=row, column=0, columnspan=2, pady=10)

# Valores por defecto
entry_masa.insert(0, "70")
entry_altura.insert(0, "1.75")
entry_edad.insert(0, "30")

root.mainloop()
