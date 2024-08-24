import sys

def main():
    if len(sys.argv) < 2:
        print("Usage: py support-scripts <script>")
        sys.exit(1)
    if sys.argv[1] == "agenda_gui":
        from agendas.generate_hbox import main as agenda_gui
        agenda_gui()
    elif sys.argv[1] == "agenda_upcusloc":
        from agendas.update_customlocs import main as agenda_upcusloc
        agenda_upcusloc()
    elif sys.argv[1] == "agenda":
        from agendas.framework import main as agenda
        agenda()
    
    
if __name__ == '__main__':
    main()