import random
import threading
import json
import os
import logging
from datetime import datetime, timedelta

# Mapping for Rank Numbers to Names
rank_name= {1: "Director", 2: "Manager", 3: "Respondant"}
data_file_permanent="call_centre.data.json" #"Hard drive for stats"

# Configuration & Logger Setup 
def load_config():
    default = {
        "call_settings": {"min_duration": 3, "max_duration": 6, "max_queue_size": 10},
        "priority_levels": {"1": "VVIP", "2": "VIP", "3": "General"},
        "system_settings": {"log_file": "call_center.log"}
    }
    if os.path.exists('config.json'):
        try:
            with open('config.json', 'r') as f: return json.load(f)
        except: return default
    return default

CONFIG = load_config()

logging.basicConfig(
    filename=CONFIG["system_settings"]["log_file"],
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class Employee():
    def __init__(self, name, id, rank, handler):# handler as from call_holder we need info that which employee is doing what and all
        self.name = name
        self.id = id
        self.rank = rank
        self.handler = handler
        self.free = True
        self.current_call = None
        self.status_lock = threading.Lock() 

    def receive_call(self, call_obj, duration):
        with self.status_lock:
            self.current_call = call_obj 
            self.free = False
        
        # Track call by ID and Name for history
        self.handler.track_employee_call(self.id, self.name, self.rank)
        logging.info(f"AGENT {self.name} (Rank {self.rank}) accepted call from {call_obj.name}")
        print(f"\n[{rank_name[self.rank]}: {self.name}] Taking call from {call_obj.name} ({duration}s)")
        threading.Timer(duration, self.end_call, [duration]).start()

    def end_call(self, duration):
        print(f"\n--- Call finished: {self.current_call.name}(Agent: {self.name}) ---")
        logging.info(f"AGENT {self.name} finished call with {self.current_call.name}")
        self.handler.call_log(self.current_call)
        self.handler.satisfaction_check(self.current_call)
        self.handler.record_avg(duration)

        with self.status_lock:
            self.free = True
            self.current_call = None
        self.handler.next_call()

    def is_free(self):
        with self.status_lock: return self.free

class Respondant(Employee):
    def __init__(self, name, id, handler): super().__init__(name, id, 3, handler)
class Manager(Employee):
    def __init__(self, name, id, handler): super().__init__(name, id, 2, handler)
class Director(Employee):
    def __init__(self, name, id, handler): super().__init__(name, id, 1, handler)

class Call():
    def __init__(self, caller_name, caller_id):
        self.name = caller_name
        self.id = caller_id
        self.code = 3 

class Call_Holder():
    def __init__(self):
        self.respondants, self.managers, self.directors = [], [], []
        self.queue = [[], [], []]
        self.call_history, self.missed, self.avg_durations = [], [], []
        self.master_id_list = []
        self.employee_stats = self.load_data()
        self.data_lock = threading.Lock()
    def save_data(self):
        with self.data_lock:
            with open(data_file_permanent,'w') as f:
                json.dump(self.employee_stats,f,indent=4)
    
    def load_data(self):
        if os.path.exists(data_file_permanent):
            try:
                with open(data_file_permanent,'r') as f: return json.load(f)
            except: return {}
        return {}
    def add_employee(self, employee):
        with self.data_lock:
            if employee.id in self.master_id_list:
                print(f"!!! Error: ID {employee.id} is already taken !!!")
                return False
            self.master_id_list.append(employee.id)
            
            if employee.rank == 3: self.respondants.append(employee)
            elif employee.rank == 2: self.managers.append(employee)
            elif employee.rank == 1: self.directors.append(employee)
            print(f"[{rank_name[employee.rank]}] {employee.name} added.")

    def track_employee_call(self, eid, name, rank):
        eid = str (eid)
        with self.data_lock:
            if eid not in self.employee_stats:
                self.employee_stats[eid] = {'name': name, 'rank': rank, 'calls': []}
            self.employee_stats[eid]['calls'].append(datetime.now().isoformat()) # isoformat for aapending datetime in form of string that json can understand
        self.save_data()

    def dispatch_call(self, call_obj):
        target_list = [self.respondants, self.managers, self.directors]
        
        # Who will take this call first based on priority
        if call_obj.code == 1: preferred_list = self.directors
        elif call_obj.code == 2: preferred_list = self.managers
        else: preferred_list = self.respondants

        # 2. Try the preferred list first, then search others if busy
        # Search through preferred_list first, then fallback to others
        search_order = [preferred_list] + [lst for lst in target_list if lst is not preferred_list]
        
        for emp_list in search_order:
            for emp in emp_list:
                if emp.is_free():
                    dur = random.randint(CONFIG["call_settings"]["min_duration"], CONFIG["call_settings"]["max_duration"])
                    emp.receive_call(call_obj, dur)
                    return

        print(f"!!! No agents available for {call_obj.name}. Adding to queue.")
        
        # 3. If no one free, check queue limit and add to queue
        with self.data_lock:
            if sum(len(q) for q in self.queue) >= CONFIG["call_settings"]["max_queue_size"]:
                print("!!! SYSTEM OVERLOAD: Call Rejected !!!")
                if call_obj.name not in self.missed: self.missed.append(call_obj.name)
                return
            
            self.queue[call_obj.code-1].append(call_obj)
            if call_obj.name not in self.missed: self.missed.append(call_obj.name)

    def next_call(self):
        with self.data_lock:
            for i in range(3):
                if self.queue[i]:
                    next_person = self.queue[i].pop(0)
                    threading.Thread(target=self.dispatch_call, args=(next_person,)).start()
                    return

    def call_log(self, call_obj):
        with self.data_lock:
            if call_obj.name not in self.call_history: self.call_history.append(call_obj.name)

    def record_avg(self, duration):
        with self.data_lock: self.avg_durations.append(duration)

    def display_performance_report(self):
        now = datetime.now()
        today = now.date()
        last_week = now - timedelta(days=7)
        last_month = now - timedelta(days=30)

        print("\n" + "="*85)
        print(f"{'EMPLOYEE PERFORMANCE REPORT':^85}")
        print("="*85)
        print(f"{'ID':6} | {'Name':15} | {'Rank':12} | {'Today':8} | {'7 Days':8} | {'30 Days':8} | {'Total':6}")
        print("-" * 85)

        with self.data_lock:
            for eid, data in self.employee_stats.items():
                # Convert ISO strings back to datetime objects for comparison
                all_calls = [datetime.fromisoformat(c) for c in data['calls']]
                c_today = len([c for c in all_calls if c.date() == today])
                c_week  = len([c for c in all_calls if c > last_week])
                c_month = len([c for c in all_calls if c > last_month])
                total   = len(all_calls)

                print(f"{eid:6} | {data['name']:15} | {rank_name[data['rank']]:12} | "
                      f"{c_today:8} | {c_week:8} | {c_month:8} | {total:6}")
        
        avg_val = sum(self.avg_durations)/len(self.avg_durations) if self.avg_durations else 0
        print("-" * 85)
        print(f"System Avg: {avg_val:.2f}s | Attended: {len(self.call_history)} | Missed: {len(self.missed)}")
        print("="*85)

    def satisfaction_check(self, call_obj):
        # Run this in a separate thread so it doesn't block the Menu
        def ask():
            ans = input(f"\n[FEEDBACK] Is customer {call_obj.name} satisfied? (y/n): ").lower().strip()
            if ans in ["n", "no"]:
                with self.data_lock:
                    if call_obj.code > 1:
                        call_obj.code -= 1
                        self.queue[call_obj.code-1].insert(0, call_obj)
                        print(f"\n>> Escalated {call_obj.name} to Priority {call_obj.code} <<")
        
        threading.Thread(target=ask, daemon=True).start()

    def search_employee_stats(self, eid):
        #One specific person's stats
        with self.data_lock:
            data = self.employee_stats.get(str(eid))
            if not data:
                print(f"--- Employee ID {eid} not found ---")
                return

            now = datetime.now()
            all_calls = [datetime.fromisoformat(c) for c in data['calls']]
            
            stats = {
                "Today": len([c for c in all_calls if c.date() == now.date()]),
                "Week":  len([c for c in all_calls if c > now - timedelta(days=7)]),
                "Month": len([c for c in all_calls if c > now - timedelta(days=30)]),
                "Total": len(all_calls)
            }

            print(f"\n--- Detailed Stats for {data['name']} (Rank: {rank_name[data['rank']]}) ---")
            for period, count in stats.items():
                print(f"{period:7}: {count} calls")

# Menu 
handler = Call_Holder()       
call_counter = 1

while True:
    print("\n--- CALL CENTER MANAGEMENT ---")
    print("1. Add Employee")
    print("2. Make a Call")
    print("3. Show Agent Status (Live)")
    print("4. Full Performance Report (All Staff)")
    print("5. Search Specific Employee Stats")
    print("6. Exit")
    
    choice = input("Select Option: ")
    
    if choice == '1':
        name, eid = input("Name: "), input("ID: ")
        rank_input = input("Rank (1:Director, 2:Manager, 3:Respondant): ")
        if rank_input == '1': handler.add_employee(Director(name, eid, handler))
        elif rank_input == '2': handler.add_employee(Manager(name, eid, handler))
        else: handler.add_employee(Respondant(name, eid, handler))

    elif choice == '2':
        c_name = input("Customer Name: ")
        handler.dispatch_call(Call(c_name, call_counter))
        call_counter += 1

    elif choice == '3':
        handler.show_employee_status()

    elif choice == '4':
        handler.display_performance_report()

    elif choice == '5':
        search_id = input("Enter Employee ID to search: ")
        handler.search_employee_stats(search_id)

    elif choice == '6':
        print("Saving data and exiting...")
        break