import tkinter as tk
from tkinter import filedialog, messagebox
import subprocess

def convert_pdf():
    input_path = filedialog.askopenfilename(filetypes=[('PDF files', '*.pdf')])
    if not input_path:
        return
    output_path = filedialog.asksaveasfilename(defaultextension='.md', filetypes=[('Markdown files', '*.md')])
    if not output_path:
        return
    try:
        subprocess.run(['python', 'pdf_to_md.py', input_path, output_path], check=True)
        messagebox.showinfo('Success', 'Conversion completed!')
    except Exception as e:
        messagebox.showerror('Error', f'Conversion failed: {str(e)}')

root = tk.Tk()
root.title('PDF to Markdown Converter')
button = tk.Button(root, text='Select PDF and Convert', command=convert_pdf, padx=20, pady=10)
button.pack(padx=50, pady=50)
root.mainloop()