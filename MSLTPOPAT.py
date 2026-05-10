import os
import re
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

def setup_clipboard_bindings(widget):
    def gen(event_name):
        return lambda e: (widget.event_generate(event_name), "break")
    widget.bind("<Control-c>", gen("<<Copy>>"))
    widget.bind("<Control-v>", gen("<<Paste>>"))
    widget.bind("<Control-x>", gen("<<Cut>>"))
    widget.bind("<Control-a>", lambda e: (widget.tag_add("sel", "1.0", "end"), "break"))
    widget.bind("<Command-c>", gen("<<Copy>>"))
    widget.bind("<Command-v>", gen("<<Paste>>"))
    widget.bind("<Command-x>", gen("<<Cut>>"))
    widget.bind("<Command-a>", lambda e: (widget.tag_add("sel", "1.0", "end"), "break"))
    widget.bind("<Button-1>", lambda e: widget.focus_set())
    menu = tk.Menu(widget, tearoff=0)
    menu.add_command(label="Копировать", command=lambda: widget.event_generate("<<Copy>>"))
    menu.add_command(label="Вставить", command=lambda: widget.event_generate("<<Paste>>"))
    menu.add_command(label="Вырезать", command=lambda: widget.event_generate("<<Cut>>"))
    menu.add_separator()
    menu.add_command(label="Выделить всё", command=lambda: widget.tag_add("sel", "1.0", "end"))
    def show_menu(event):
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
    widget.bind("<Button-3>", show_menu)
    widget.bind("<Control-Button-1>", show_menu)

def compress_lines(lines, n):
    """
    Сжимает строки: каждые N следующих строк поднимает на предыдущую.
    
    Пример (N=2):
      Исходные строки:       Результат:
      12 44 55               12 44 55 1 2 3 4 5 6 7 8
      1 2 3 4                9 10 11 12 13 14 15 16
      5 6 7 8
      9 10 11 12
      13 14 15 16
    """
    if n <= 0:
        return lines[:]
    
    result = []
    i = 0
    while i < len(lines):
        base = lines[i].strip()
        # Собираем N следующих строк на текущую
        for j in range(1, n + 1):
            if i + j < len(lines):
                base += " " + lines[i + j].strip()
        result.append(base)
        # Пропускаем N обработанных строк
        i += n + 1
    
    return result

def load_file():
    """Загружает текстовый файл."""
    path = filedialog.askopenfilename(
        filetypes=[("Text files", "*.txt;*.csv"), ("All files", "*.*")]
    )
    if not path:
        return
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось прочитать файл:\n{e}")
        return
    
    app.raw_content = content
    app.filepath = path
    
    input_text.delete("1.0", tk.END)
    input_text.insert("1.0", content)
    
    status_var.set(f"Файл загружен: {os.path.basename(path)} | Строк: {len(content.strip().splitlines())}")
    
    do_compress()

def do_compress():
    """Выполняет сжатие строк с параметром N."""
    try:
        n = int(n_var.get())
        if n < 1:
            messagebox.showwarning("Предупреждение", "N должно быть >= 1")
            return
    except ValueError:
        messagebox.showwarning("Ошибка", "Введите целое число N")
        return
    
    if not hasattr(app, 'raw_content') or not app.raw_content.strip():
        messagebox.showinfo("Информация", "Сначала загрузите файл")
        return
    
    lines = app.raw_content.strip().splitlines()
    compressed = compress_lines(lines, n)
    
    output_text.delete("1.0", tk.END)
    output_text.insert("1.0", "\n".join(compressed))
    
    info_var.set(f"Исходных строк: {len(lines)} → После сжатия (N={n}): {len(compressed)}")

def save_result():
    """Сохраняет результат в файл."""
    content = output_text.get("1.0", tk.END).strip()
    if not content:
        messagebox.showinfo("Информация", "Нет результата для сохранения")
        return
    
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if not path:
        return
    
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        messagebox.showinfo("Успех", f"Результат сохранён:\n{path}")
    except Exception as e:
        messagebox.showerror("Ошибка", f"Не удалось сохранить файл:\n{e}")

def clear_all():
    """Очищает все поля."""
    input_text.delete("1.0", tk.END)
    output_text.delete("1.0", tk.END)
    n_var.set("2")
    status_var.set("Готов")
    info_var.set("")
    if hasattr(app, 'raw_content'):
        del app.raw_content
    if hasattr(app, 'filepath'):
        del app.filepath

def on_n_change(*args):
    """Автоматически пересчитывает при изменении N."""
    do_compress()

# ============================================================
# ГРАФИЧЕСКИЙ ИНТЕРФЕЙС
# ============================================================
app = tk.Tk()
app.title("Компрессор строк — объединение строк по N")
app.geometry("900x700")

# ========== ЗАГОЛОВОК ==========
header = tk.Label(
    app,
    text="=== КОМПРЕССОР СТРОК: ОБЪЕДИНЕНИЕ N СТРОК НА ПРЕДЫДУЩУЮ ===",
    font=("Arial", 13, "bold"), pady=8
)
header.pack(fill=tk.X)

# ========== ПАНЕЛЬ УПРАВЛЕНИЯ ==========
control_frame = tk.Frame(app)
control_frame.pack(fill=tk.X, padx=10, pady=6)

load_btn = tk.Button(
    control_frame, text="📂 Загрузить файл", command=load_file,
    bg="#4a90d9", fg="white", padx=12, pady=3
)
load_btn.pack(side=tk.LEFT, padx=(0, 10))

tk.Label(control_frame, text="N =", font=("Arial", 11, "bold")).pack(side=tk.LEFT, padx=(0, 3))
n_var = tk.StringVar(value="2")
n_var.trace_add("write", on_n_change)
n_entry = tk.Entry(control_frame, textvariable=n_var, width=5, font=("Arial", 11))
n_entry.pack(side=tk.LEFT, padx=(0, 5))

tk.Label(control_frame, text="(строк на предыдущую)", fg="#888",
         font=("Arial", 9)).pack(side=tk.LEFT, padx=(0, 15))

compress_btn = tk.Button(
    control_frame, text="🔄 Сжать", command=do_compress,
    bg="#5cb85c", fg="white", padx=12, pady=3
)
compress_btn.pack(side=tk.LEFT, padx=(0, 8))

save_btn = tk.Button(
    control_frame, text="💾 Сохранить результат", command=save_result,
    bg="#f0ad4e", fg="white", padx=12, pady=3
)
save_btn.pack(side=tk.LEFT, padx=(0, 8))

clear_btn = tk.Button(
    control_frame, text="🗑 Очистить", command=clear_all,
    bg="#d9534f", fg="white", padx=12, pady=3
)
clear_btn.pack(side=tk.LEFT)

# ========== СТАТУСНАЯ СТРОКА ==========
status_var = tk.StringVar(value="Готов")
status_bar = tk.Label(
    app, textvariable=status_var, anchor="w", padx=12, pady=2,
    bg="#e8e8e8", font=("Arial", 9)
)
status_bar.pack(fill=tk.X, padx=10, pady=(4, 0))

info_var = tk.StringVar(value="")
info_bar = tk.Label(
    app, textvariable=info_var, anchor="w", padx=12, pady=2,
    bg="#fff3cd", fg="#856404", font=("Arial", 9)
)
info_bar.pack(fill=tk.X, padx=10, pady=(2, 4))

# ========== ОСНОВНАЯ ОБЛАСТЬ (две колонки) ==========
main_frame = tk.Frame(app)
main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=4)

main_frame.grid_columnconfigure(0, weight=1, uniform="col")
main_frame.grid_columnconfigure(1, weight=1, uniform="col")
main_frame.grid_rowconfigure(0, weight=1)

# --- ЛЕВАЯ КОЛОНКА: Исходный текст ---
left_frame = tk.Frame(main_frame, relief=tk.SOLID, bd=1)
left_frame.grid(row=0, column=0, padx=(0, 5), pady=2, sticky="nsew")

tk.Label(left_frame, text="📄 Исходный текст", font=("Arial", 10, "bold"),
         bg="#f0f0f0", pady=3).pack(fill=tk.X)

input_text = tk.Text(left_frame, wrap=tk.NONE, font=("Consolas", 10), padx=8, pady=8)
in_yscroll = tk.Scrollbar(left_frame, orient=tk.VERTICAL, command=input_text.yview)
in_xscroll = tk.Scrollbar(left_frame, orient=tk.HORIZONTAL, command=input_text.xview)
input_text.configure(yscrollcommand=in_yscroll.set, xscrollcommand=in_xscroll.set)
in_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
in_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
input_text.pack(fill=tk.BOTH, expand=True)
setup_clipboard_bindings(input_text)

# --- ПРАВАЯ КОЛОНКА: Результат ---
right_frame = tk.Frame(main_frame, relief=tk.SOLID, bd=1)
right_frame.grid(row=0, column=1, padx=(5, 0), pady=2, sticky="nsew")

tk.Label(right_frame, text="✅ Результат сжатия", font=("Arial", 10, "bold"),
         bg="#e8f5e9", fg="#2e7d32", pady=3).pack(fill=tk.X)

output_text = tk.Text(right_frame, wrap=tk.NONE, font=("Consolas", 10),
                      bg="#fafff0", padx=8, pady=8)
out_yscroll = tk.Scrollbar(right_frame, orient=tk.VERTICAL, command=output_text.yview)
out_xscroll = tk.Scrollbar(right_frame, orient=tk.HORIZONTAL, command=output_text.xview)
output_text.configure(yscrollcommand=out_yscroll.set, xscrollcommand=out_xscroll.set)
out_yscroll.pack(side=tk.RIGHT, fill=tk.Y)
out_xscroll.pack(side=tk.BOTTOM, fill=tk.X)
output_text.pack(fill=tk.BOTH, expand=True)
setup_clipboard_bindings(output_text)

# ========== НИЖНЯЯ ПАНЕЛЬ: ПРИМЕР ==========
example_frame = tk.Frame(app, bg="#f9f9f9", relief=tk.SOLID, bd=1)
example_frame.pack(fill=tk.X, padx=10, pady=(4, 10))

example_text = """📌 ПРИМЕР РАБОТЫ (N=2):

  Исходный файл:                  Результат:
  ─────────────────────────       ─────────────────────────
  12 44 55                        12 44 55 1 2 3 4 5 6 7 8
  1 2 3 4                         9 10 11 12 13 14 15 16
  5 6 7 8
  9 10 11 12
  13 14 15 16

  💡 КАК ЭТО РАБОТАЕТ:
     - Берётся 1-я строка → к ней дописываются следующие N=2 строки
     - Потом 4-я строка → к ней дописываются 5-я и 6-я
     - И так далее..."""

lbl_example = tk.Label(example_frame, text=example_text, anchor="w", justify=tk.LEFT,
                       font=("Consolas", 9), fg="#555", padx=12, pady=8)
lbl_example.pack(fill=tk.X)

# ========== ЗАПУСК ==========
app.mainloop()
