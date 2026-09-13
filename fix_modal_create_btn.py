import sys

path = "index.html"
with open(path, "r", encoding="utf-8") as f:
    content = f.read()

def do_replace(label, old, new, expected=1):
    global content
    c = content.count(old)
    if c != expected:
        print(f"ABORT [{label}]: found {c} times, expected {expected}")
        sys.exit(1)
    content = content.replace(old, new, 1)

old = '''    durInput.disabled = false;
    document.getElementById("cal-modal-remove").textContent = "Abbrechen";
    document.getElementById("cal-modal-backdrop").hidden = false;
    nameInput.focus();'''
new = '''    durInput.disabled = false;
    document.getElementById("cal-modal-remove").hidden = true;
    document.getElementById("cal-modal-backdrop").hidden = false;
    nameInput.focus();'''
do_replace("hide-remove-in-create", old, new)

old2 = '''    document.getElementById("cal-modal-remove").textContent = isCustom ? "L\\u00f6schen" : (isGoal ? "Diese Woche auslassen" : "Position zur\\u00fccksetzen");
    document.getElementById("cal-modal-backdrop").hidden = false;
    document.getElementById("cal-modal-date").focus();'''
new2 = '''    document.getElementById("cal-modal-remove").hidden = false;
    document.getElementById("cal-modal-remove").textContent = isCustom ? "L\\u00f6schen" : (isGoal ? "Diese Woche auslassen" : "Position zur\\u00fccksetzen");
    document.getElementById("cal-modal-backdrop").hidden = false;
    document.getElementById("cal-modal-date").focus();'''
do_replace("show-remove-in-move", old2, new2)

with open(path, "w", encoding="utf-8") as f:
    f.write(content)

print("OK: modal create-mode button fix applied")
