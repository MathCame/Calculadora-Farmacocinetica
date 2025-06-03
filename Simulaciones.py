import numpy as np
from scipy.integrate import odeint
import matplotlib.pyplot as plt
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import colorsys

# ----- Funciones modelo f y g -----
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
    intervalo = max(4, min(intervalo, 24))
    return intervalo

def generar_colores(n):
    colores = []
    for i in range(n):
        hue = i / n
        saturation = 0.9
        value = 0.9
        r, g, b = colorsys.hsv_to_rgb(hue, saturation, value)
        colores.append((r, g, b))
    return colores

# ------ Simulación periódica ------
def simular_dosis_multiples(params, medicamento, num_dosis=5, puntos_por_ciclo=150):
    intervalo = calcular_intervalo_dosificacion(params, medicamento)
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
        y0[1] += 100  # Nueva dosis
        t_total += intervalo
    t = np.concatenate(t_segmentos)
    sol = np.concatenate(sol_segmentos, axis=0)
    return t, sol, intervalo

def simular_poblacion(medicamento, n_pacientes=100):
    np.random.seed(42)
    pacientes = []
    resultados = []
    for _ in range(n_pacientes):
        masa = np.random.uniform(50, 100)
        altura = np.random.uniform(1.5, 2.0)
        edad = np.random.randint(18, 80)
        genero = np.random.choice(["Hombre", "Mujer"])
        comorbilidad = np.random.choice(lista_comorbilidades)
        genetica = np.random.choice(lista_genetica)
        alergia = np.random.choice(lista_alergia)
        imc = masa / (altura ** 2)
        genetica_factor = 0.2 if genetica == "Metabolizador rápido" else (-0.2 if genetica == "Metabolizador lento" else 0)
        alergia_factor = 0.1 if alergia == "Alergia leve" else (0.2 if alergia == "Alergia moderada" else (0.3 if alergia == "Alergia severa" else 0))
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
        t, sol, intervalo = simular_dosis_multiples(params, medicamento)
        pacientes.append(params)
        resultados.append((t, sol, intervalo))
    return pacientes, resultados

# --- Interfaz gráfica y visualización ---
def visualizar_poblacion():
    try:
        n_pacientes = int(entry_n_pacientes.get())
        if n_pacientes < 1 or n_pacientes > 1000:
            raise ValueError
    except:
        messagebox.showerror("Error", "Ingrese un número de pacientes válido (1-1000)")
        return

    medicamento = medicamento_var.get()
    pacientes, resultados = simular_poblacion(medicamento, n_pacientes)
    colores = generar_colores(n_pacientes)
    intervalos = [r[2] for r in resultados]
    promedio = np.mean(intervalos)
    minimo = np.min(intervalos)
    maximo = np.max(intervalos)

    graph_window = tk.Toplevel(root)
    graph_window.title(f"Órbitas periódicas de {n_pacientes} pacientes - {medicamento}")
    graph_window.geometry("1000x700")
    import matplotlib
    matplotlib.use('TkAgg')
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

    fig, ax = plt.subplots(figsize=(10,6), dpi=100)
    for i, ((t, sol, intervalo), color) in enumerate(zip(resultados, colores)):
        C, V = sol[:,0], sol[:,2]
        ax.plot(C, V, color=color, alpha=0.65)
    ax.set_xlabel('Concentración (C)')
    ax.set_ylabel('Volumen (V)')
    ax.set_title(f'Órbitas periódicas (dosis múltiples) de {n_pacientes} pacientes\n{medicamento}')
    ax.grid(True)

    stats_text = f"Intervalo promedio: {promedio:.2f} h\nMínimo: {minimo:.2f} h\nMáximo: {maximo:.2f} h"
    plt.figtext(0.77, 0.15, stats_text, fontsize=12, bbox={"facecolor":"#f0f0f0", "alpha":0.8})

    canvas = FigureCanvasTkAgg(fig, master=graph_window)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=1)

    def guardar_figura():
        file_path = filedialog.asksaveasfilename(defaultextension='.png', filetypes=[("PNG","*.png"),("PDF","*.pdf"),("All Files","*.*")])
        if file_path:
            fig.savefig(file_path)
            messagebox.showinfo("Guardado", f"Gráfico guardado en {file_path}")

    btn_guardar = ttk.Button(graph_window, text="Guardar Gráfico", command=guardar_figura)
    btn_guardar.pack(pady=10)

# --- Interfaz principal ---
root = tk.Tk()
root.title("Simulación Farmacocinética Poblacional (Dosis Múltiples)")

main_frame = ttk.Frame(root, padding="20 20 20 20")
main_frame.pack(fill=tk.BOTH, expand=True)

lista_medicamentos = ["Ibuprofeno", "Paracetamol", "Aspirina", "Amoxicilina", "Metformina", "Loratadina"]
lista_comorbilidades = ["Sin comorbilidad", "Diabetes", "Insuficiencia renal", "Insuficiencia hepática", "Hipertensión", "Asma"]
lista_genetica = ["Metabolizador normal", "Metabolizador rápido", "Metabolizador lento", "No identificado"]
lista_alergia = ["Sin alergia", "Alergia leve", "Alergia moderada", "Alergia severa"]

medicamento_var = tk.StringVar(value=lista_medicamentos[0])
ttk.Label(main_frame, text="Medicamento:").grid(row=0, column=0, sticky='e', pady=5)
ttk.OptionMenu(main_frame, medicamento_var, lista_medicamentos[0], *lista_medicamentos).grid(row=0, column=1, pady=5, sticky='w')

ttk.Label(main_frame, text="Número de pacientes:").grid(row=1, column=0, sticky='e', pady=5)
entry_n_pacientes = ttk.Entry(main_frame, width=10)
entry_n_pacientes.insert(0, "100")
entry_n_pacientes.grid(row=1, column=1, pady=5, sticky='w')

ttk.Button(main_frame, text="Ejecutar Simulación Poblacional", command=visualizar_poblacion).grid(row=2, column=0, columnspan=2, pady=20)

root.mainloop()

