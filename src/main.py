import re
import json
import datetime
import argparse
import os
from typing import List, Dict, Any, Optional
from ics import Calendar, Event
from zoneinfo import ZoneInfo

# building map
BUILDING_MAP = {
    "AL": "Arts Lecture Hall (AL)",
    "BMH": "B.C. Matthews Hall (BMH)",
    "CGR": "Conrad Grebel University College (CGR)",
    "CIF": "Columbia Icefield (CIF)",
    "CPH": "Carl A. Pollock Hall (CPH)",
    "DC": "William G. Davis Computer Research Centre (DC)",
    "DWE": "Douglas Wright Engineering Building (DWE)",
    "E2": "Engineering 2 (E2)",
    "E3": "Engineering 3 (E3)",
    "E5": "Engineering 5 (E5)",
    "E6": "Engineering 6 (E6)",
    "E7": "Engineering 7 (E7)",
    "EIT": "Centre for Environmental & Information Technology (EIT)",
    "ESC": "Earth Sciences & Chemistry (ESC)",
    "EV1": "Environment 1 (EV1)",
    "EV2": "Environment 2 (EV2)",
    "EV3": "Environment 3 (EV3)",
    "FED": "Federation Hall (FED)",
    "GH": "Graduate House (GH)",
    "GSC": "General Services Complex (GSC)",
    "HH": "J.G. Hagey Hall of the Humanities (HH)",
    "HS": "Health Services (HS)",
    "LIB": "Dana Porter Library (LIB)",
    "M3": "Mathematics 3 (M3)",
    "MC": "Mathematics & Computer Building (MC)",
    "MHR": "Minota Hagey Residence (MHR)",
    "ML": "Modern Languages (ML)",
    "OPT": "School of Optometry and Vision Science (OPT)",
    "PAC": "Physical Activities Complex (PAC)",
    "PAS": "Psychology, Anthropology, and Sociology (PAS)",
    "PHY": "Physics (PHY)",
    "PSE": "Pearl Sullivan Engineering Building (PSE)",
    "QNC": "Mike & Ophelia Lazaridis Quantum-Nano Centre (QNC)",
    "RCH": "J.R. Coutts Engineering Lecture Hall (RCH)",
    "REN": "Renison University College (REN)",
    "SLC": "Student Life Centre (SLC)",
    "STC": "Science Teaching Complex (STC)",
    "TH": "Tatham Centre (TH)",
    "UWP": "University of Waterloo Place (UWP)",
    "V1": "Village 1 (V1)",
    "WEM": "William M. Tatham Centre (WEM)",
}

# day map for display and rrule
DAY_MAP_FULL = {'M': 'monday', 'T': 'tuesday', 'W': 'wednesday', 'Th': 'thursday', 'F': 'friday', 'S': 'saturday', 'Su': 'sunday'}
DAY_MAP_RRULE = {'M': 'MO', 'T': 'TU', 'W': 'WE', 'Th': 'TH', 'F': 'FR', 'S': 'SA', 'Su': 'SU'}
DAY_INTS = {'M': 0, 'T': 1, 'W': 2, 'Th': 3, 'F': 4, 'S': 5, 'Su': 6}

def parse_schedule(text: str) -> List[Dict[str, Any]]:
    parsed_slots = []
    
    # regex definitions
    course_re = re.compile(r'([A-Z]{2,5}\s+\d{3}[A-Z]?)\s+-\s+([^\r\n]+)')
    class_header_re = re.compile(r'(\d{4,5})\s+(\d{3})\s+([A-Z]{3})\s+')
    date_range_re = re.compile(r'(\d{2}/\d{2}/\d{4})\s*-\s*(\d{2}/\d{2}/\d{4})')
    time_re = re.compile(r'(\d{1,2}:\d{2}[AP]M)\s*-\s*(\d{1,2}:\d{2}[AP]M)')
    days_re = re.compile(r'([MThWF]{1,6})')

    # find all courses
    course_matches = list(course_re.finditer(text))
    
    for i, match in enumerate(course_matches):
        course_code = match.group(1).strip()
        course_name = match.group(2).strip() # kept if needed
        
        start_idx = match.end()
        end_idx = course_matches[i+1].start() if i + 1 < len(course_matches) else len(text)
        course_block = text[start_idx:end_idx]
        
        # find classes in course block
        class_matches = list(class_header_re.finditer(course_block))
        
        for j, c_match in enumerate(class_matches):
            class_num = c_match.group(1)
            section = c_match.group(2)
            component = c_match.group(3)
            
            # ignore TST
            if component == 'TST':
                continue
            
            c_start = c_match.end()
            c_end = class_matches[j+1].start() if j + 1 < len(class_matches) else len(course_block)
            class_body = course_block[c_start:c_end]
            
            # extract slots by finding date ranges
            date_matches = list(date_range_re.finditer(class_body))
            last_end = 0
            
            for d_match in date_matches:
                date_start_str = d_match.group(1)
                date_end_str = d_match.group(2)
                
                # slot text is everything before the date range
                slot_text = class_body[last_end:d_match.start()].strip()
                last_end = d_match.end()
                
                current_days = []
                start_time = None
                end_time = None
                location_full = "TBA"
                location_code = ""
                instructor = "TBA"
                
                # find time
                t_match = time_re.search(slot_text)
                if t_match:
                    start_time = t_match.group(1)
                    end_time = t_match.group(2)
                    
                    # days before time
                    pre_time = slot_text[:t_match.start()].strip()
                    d_match_days = days_re.search(pre_time)
                    if d_match_days:
                         days_str = d_match_days.group(1)
                         days_map = []
                         if 'Su' in days_str: days_map.append('Su'); days_str = days_str.replace('Su','')
                         if 'M' in days_str: days_map.append('M')
                         if 'Th' in days_str: days_map.append('Th'); days_str = days_str.replace('Th','')
                         if 'T' in days_str: days_map.append('T')
                         if 'W' in days_str: days_map.append('W')
                         if 'F' in days_str: days_map.append('F')
                         if 'S' in days_str: days_map.append('S')
                         current_days = days_map
                    
                    # location and instructor after time
                    post_time = slot_text[t_match.end():].strip()
                    parts = [p.strip() for p in post_time.split('\n') if p.strip()]
                    
                    if parts:
                        location_code = parts[0]
                        if len(parts) > 1:
                            instructor = ", ".join(parts[1:])
                        else:
                            instructor = ""

                # resolve building name
                loc_parts = location_code.split()
                if loc_parts:
                    bldg_code = loc_parts[0]
                    if bldg_code in BUILDING_MAP:
                        full_name = BUILDING_MAP[bldg_code]
                        location_full = full_name
                    else:
                        location_full = location_code # fallback
                
                # Only add if valid time info found
                if start_time and end_time and current_days:
                    parsed_slots.append({
                        "course": course_code,
                        "component": component,
                        "section": section,
                        "days": current_days,
                        "start_time": start_time,
                        "end_time": end_time,
                        "location_full": location_full,
                        "location_code_room": location_code,
                        "instructor": instructor,
                        "date_start": date_start_str,
                        "date_end": date_end_str
                    })

    return parsed_slots

def format_time_str(slot: Dict[str, Any], lower: bool = False) -> str:
    # "8:30 am - 9:50 am, weekly on tuesday and thursday from 1/5/2026 to 2/13/2026"
    days_str = " and ".join([DAY_MAP_FULL[d] for d in slot['days']])
    t_str = f"{slot['start_time']} - {slot['end_time']}, weekly on {days_str} from {slot['date_start']} to {slot['date_end']}"
    return t_str.lower() if lower else t_str

def generate_ics(slots: List[Dict[str, Any]], lower: bool = False) -> str:
    c = Calendar()
    tz = ZoneInfo("America/Toronto")
    
    for slot in slots:
        e = Event()
        
        name_str = f"{slot['course']} {slot['component']}"
        desc_str = f"{slot['location_code_room']}\n{slot['instructor']}".strip()
        
        e.name = name_str.lower() if lower else name_str
        e.location = slot['location_full']
        e.description = desc_str.lower() if lower else desc_str
        
        # calculate start/end datetime of FIRST occurrence
        # parse dates
        m, d, y = map(int, slot['date_start'].split('/'))
        start_date_obj = datetime.date(y, m, d)
        
        # apply timezone to recurrence end date
        em, ed, ey = map(int, slot['date_end'].split('/'))
        end_date_obj = datetime.date(ey, em, ed)
        
        # parse times
        # 10:00AM -> format %I:%M%p
        st_dt = datetime.datetime.strptime(slot['start_time'], "%I:%M%p")
        et_dt = datetime.datetime.strptime(slot['end_time'], "%I:%M%p")
        
        # find first day that matches one of the days
        # start_date_obj weekday() returns 0=Mon
        valid_days = [DAY_INTS[d] for d in slot['days']]
        
        # loop until end_date_obj to find all occurrences
        # flattening events instead of RRULE for simplicity and correctness with timezones
        
        curr = start_date_obj
        while curr <= end_date_obj:
            if curr.weekday() in valid_days:
                # create a single instance
                inst = Event()
                inst.name = e.name
                inst.location = e.location
                inst.description = e.description
                
                # Create timezone-aware datetimes
                # combine(date, time) -> naive
                # replace(tzinfo=tz) -> aware
                dt_start = datetime.datetime.combine(curr, st_dt.time()).replace(tzinfo=tz)
                dt_end = datetime.datetime.combine(curr, et_dt.time()).replace(tzinfo=tz)
                
                inst.begin = dt_start
                inst.end = dt_end
                c.events.add(inst)
            curr += datetime.timedelta(days=1)

    return c.serialize()

def main():
    parser = argparse.ArgumentParser(description='Quest to Calendar converter')
    parser.add_argument('--lower', action='store_true', help='Lowercase output for names and notes')
    parser.add_argument('--test', action='store_true', help='Generate JSON output for testing')
    args = parser.parse_args()

    try:
        with open("src/input.txt", "r") as f:
            content = f.read()
        
        parsed_slots = parse_schedule(content)
        
        # prepare output directory
        output_dir = "outputs"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # format for json - ONLY IF TEST ARG IS PRESENT
        if args.test:
            json_output = []
            for slot in parsed_slots:
                name_str = f"{slot['course']} {slot['component']}"
                notes_str = f"{slot['location_code_room']}\n{slot['instructor']}".strip()
                
                json_output.append({
                    "name": name_str.lower() if args.lower else name_str,
                    "time": format_time_str(slot, lower=args.lower),
                    "location": slot['location_full'],
                    "notes": notes_str.lower() if args.lower else notes_str
                })
                
            print(f"parsed {len(json_output)} class slots")
            
            json_path = os.path.join(output_dir, "schedule.json")
            with open(json_path, "w") as f:
                json.dump(json_output, f, indent=4)
            print(f"saved to {json_path}")
        else:
             print(f"parsed {len(parsed_slots)} class slots")
        
        # generate ics (always)
        ics_content = generate_ics(parsed_slots, lower=args.lower)
        ics_path = os.path.join(output_dir, "schedule.ics")
        with open(ics_path, "w") as f:
            f.write(ics_content)
        print(f"saved to {ics_path}")

            
    except FileNotFoundError:
        print("error: src/input.txt not found.")
    except Exception as e:
        print(f"error parsing schedule: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
