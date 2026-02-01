import tkinter as tk
from tkinter import messagebox

# ================= AI DIETICIAN LOGIC =================

def calculate_bmi(weight, height_cm):
    h = height_cm / 100
    return round(weight / (h * h), 2)

def calorie_requirement(weight, goal):
    if goal == "Lose Weight":
        return int(weight * 25)
    elif goal == "Gain Weight":
        return int(weight * 35)
    else:
        return int(weight * 30)

def diet_recommendation(bmi):
    if bmi < 18.5:
        return "Underweight: Eat calorie-dense & protein-rich foods"
    elif bmi < 25:
        return "Normal: Balanced diet with protein, carbs, fats"
    elif bmi < 30:
        return "Overweight: High-fiber, low-fat meals"
    else:
        return "Obese: Strict calorie control & vegetables"

def chatbot_reply(msg, bmi, goal, weight):
    msg = msg.lower().strip()

    if msg in ["hi", "hello"]:
        return "Ask me about diet, protein, calories, breakfast, or weight goals"

    if "protein" in msg:
        return "Eggs, chicken, paneer, dal, tofu, milk"

    if "breakfast" in msg:
        return "Oats, fruits, eggs, sprouts, smoothies"

    if "junk" in msg:
        return "Avoid junk food, fried snacks, and sugary drinks"

    if "diet" in msg:
        return diet_recommendation(bmi)

    if "calorie" in msg:
        return f"Your daily calories: {calorie_requirement(weight, goal)} kcal"

    return "I didn't get that. Ask about diet, protein, calories, or breakfast."

# ================= GUI =================

root = tk.Tk()
root.title("AI Dietician & Calorie Coach")
root.geometry("520x650")
root.resizable(False, False)

tk.Label(root, text="AI Dietician & Calorie Coach",
         font=("Arial", 16, "bold")).pack(pady=10)

# ---------- INPUT ----------
tk.Label(root, text="Weight (kg)").pack()
weight_entry = tk.Entry(root)
weight_entry.pack()

tk.Label(root, text="Height (cm)").pack()
height_entry = tk.Entry(root)
height_entry.pack()

tk.Label(root, text="Goal").pack()
goal_var = tk.StringVar(value="Maintain Weight")
tk.OptionMenu(root, goal_var,
              "Lose Weight", "Maintain Weight", "Gain Weight").pack()

result_label = tk.Label(root, text="", font=("Arial", 11))
result_label.pack(pady=10)

bmi = None
weight = None
goal = None

def calculate():
    global bmi, weight, goal
    try:
        weight = float(weight_entry.get())
        height = float(height_entry.get())
        goal = goal_var.get()

        bmi = calculate_bmi(weight, height)
        calories = calorie_requirement(weight, goal)
        diet = diet_recommendation(bmi)

        result_label.config(
            text=f"BMI: {bmi}\nCalories: {calories} kcal\n{diet}"
        )
    except:
        messagebox.showerror("Error", "Enter valid numbers")

tk.Button(root, text="Calculate",
          bg="green", fg="white",
          command=calculate).pack(pady=5)

# ---------- CHAT INPUT ----------
chat_entry = tk.Entry(root, width=50, fg="gray")
chat_entry.pack(pady=10)
chat_entry.insert(0, "Type hi to start chatting…")

def clear_placeholder(event):
    if chat_entry.get() == "Type hi to start chatting…":
        chat_entry.delete(0, tk.END)
        chat_entry.config(fg="black")

def restore_placeholder(event):
    if chat_entry.get() == "":
        chat_entry.insert(0, "Type hi to start chatting…")
        chat_entry.config(fg="gray")

chat_entry.bind("<FocusIn>", clear_placeholder)
chat_entry.bind("<FocusOut>", restore_placeholder)

# ---------- CHAT OUTPUT (NO CURSOR) ----------
chat_box = tk.Text(root, height=12, width=60, state="disabled")
chat_box.pack(pady=5)

def chat():
    if bmi is None:
        messagebox.showinfo("Info", "Please calculate BMI first")
        return

    msg = chat_entry.get()
    if not msg or msg == "Type hi to start chatting…":
        return

    reply = chatbot_reply(msg, bmi, goal, weight)

    chat_box.config(state="normal")
    chat_box.insert(tk.END, f"You: {msg}\nDietician: {reply}\n\n")
    chat_box.config(state="disabled")

    chat_entry.delete(0, tk.END)

def reset_chat():
    chat_box.config(state="normal")
    chat_box.delete("1.0", tk.END)
    chat_box.config(state="disabled")

    chat_entry.delete(0, tk.END)
    chat_entry.insert(0, "Type hi to start chatting…")
    chat_entry.config(fg="gray")

# ---------- BUTTONS ----------
btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

tk.Button(btn_frame, text="Send",
          bg="blue", fg="white",
          command=chat).pack(side="left", padx=5)

tk.Button(btn_frame, text="Reset Chat",
          bg="red", fg="white",
          command=reset_chat).pack(side="left", padx=5)

root.mainloop()
