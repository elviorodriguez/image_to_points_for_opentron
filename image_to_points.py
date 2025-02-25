import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import matplotlib.transforms as mtransforms
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import sys

class PointCollectorApp:
    def __init__(self, root, image_path):
        self.root = root
        self.image_path = image_path
        self.current_rotation = 0
        self.points = []
        self.colors = ["Red", "Green", "Blue", "Orange", "Yellow"]
        self.selected_color = tk.StringVar(value=self.colors[0])
        self.selected_size = tk.IntVar(value=1)
        
        # Cargar imagen
        self.image = plt.imread(image_path)
        self.height, self.width = self.image.shape[:2]
        
        # Configurar GUI
        self.setup_gui()
        
    def setup_gui(self):
        # Configurar figura de Matplotlib
        self.fig = Figure()
        self.ax = self.fig.add_subplot(111)
        self.ax.set_aspect('equal')
        
        # Mostrar imagen centrada
        self.extent = (-self.width/2, self.width/2, -self.height/2, self.height/2)
        self.im = self.ax.imshow(self.image, extent=self.extent)
        
        # Círculo de referencia
        self.circle = plt.Circle((0, 0), 40, edgecolor='r', facecolor='none')
        self.ax.add_artist(self.circle)
        
        # Canvas de Matplotlib
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Barra de herramientas de navegación
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        
        # Controles
        controls_frame = ttk.Frame(self.root)
        controls_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Control de rotación
        ttk.Label(controls_frame, text="Rotación (°):").pack(side=tk.LEFT)
        self.rotation_slider = ttk.Scale(controls_frame, from_=0, to=360, 
                                      command=lambda v: self.update_rotation(float(v)))
        self.rotation_slider.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # Selector de color
        ttk.Label(controls_frame, text="Color:").pack(side=tk.LEFT)
        color_combo = ttk.Combobox(controls_frame, textvariable=self.selected_color, values=self.colors)
        color_combo.pack(side=tk.LEFT)
        
        # Selector de tamaño
        ttk.Label(controls_frame, text="Tamaño:").pack(side=tk.LEFT)
        size_spin = ttk.Spinbox(controls_frame, from_=1, to=5, textvariable=self.selected_size)
        size_spin.pack(side=tk.LEFT)
        
        # Botón de exportación
        export_btn = ttk.Button(controls_frame, text="Exportar Puntos", command=self.export_points)
        export_btn.pack(side=tk.RIGHT)
        
        # Tabla de puntos
        self.tree = ttk.Treeview(controls_frame, columns=("Color", "X", "Y", "Size"), show="headings")
        self.tree.heading("Color", text="Color")
        self.tree.heading("X", text="X")
        self.tree.heading("Y", text="Y")
        self.tree.heading("Size", text="Tamaño")
        self.tree.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # Evento de clic
        self.canvas.mpl_connect('button_press_event', self.on_click)
        
    def update_rotation(self, angle):
        self.current_rotation = angle
        # Aplicar transformación de rotación
        trans = mtransforms.Affine2D().rotate_deg(angle) + self.ax.transData
        self.im.set_transform(trans)
        self.canvas.draw_idle()
        
    def on_click(self, event):
        if event.inaxes != self.ax:
            return
        
        # Convertir coordenadas rotadas a originales
        theta = np.radians(-self.current_rotation)
        x_orig = event.xdata * np.cos(theta) - event.ydata * np.sin(theta)
        y_orig = event.xdata * np.sin(theta) + event.ydata * np.cos(theta)
        
        # Verificar si está dentro del círculo
        if x_orig**2 + y_orig**2 <= 40**2:
            color = self.selected_color.get()
            size = self.selected_size.get()
            
            # Agregar punto
            self.points.append({
                "Color": color,
                "X": round(x_orig, 2),
                "Y": round(y_orig, 2),
                "Size": size
            })
            
            # Actualizar tabla
            self.tree.insert("", tk.END, values=(color, round(x_orig, 2), round(y_orig, 2), size))
            
            # Dibujar punto
            self.ax.scatter(x_orig, y_orig, s=size*20, c=color.lower(), edgecolors='black')
            self.canvas.draw_idle()
            
    def export_points(self):
        if not self.points:
            return
        
        # Exportar CSV
        df = pd.DataFrame(self.points)
        df.to_csv("puntos.csv", index=False)
        
        # Generar gráfico de dispersión
        fig, ax = plt.subplots()
        for color in self.colors:
            subset = df[df["Color"] == color]
            if not subset.empty:
                ax.scatter(subset["X"], subset["Y"], s=subset["Size"]*20, 
                          c=color.lower(), label=color)
        
        ax.set_xlim(-40, 40)
        ax.set_ylim(-40, 40)
        ax.set_aspect('equal')
        ax.grid(True)
        ax.legend()
        plt.title("Puntos registrados")
        plt.savefig("grafico_puntos.png")
        plt.close()
        
        print("Datos exportados: puntos.csv y grafico_puntos.png")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: image_to_points.py <imagen.png>")
        sys.exit(1)
    
    root = tk.Tk()
    root.title("Image to Points Converter")
    app = PointCollectorApp(root, sys.argv[1])
    root.mainloop()