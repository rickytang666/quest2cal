import re
import json
import datetime
from typing import List, Dict, Any, Optional

# building map
BUILDING_MAP = {
    "AL": "Arts Lecture Hall (AL)",
    "BMH": "B.C. Matthews Hall (BMH)",
    "CGR": "Conrad Grebel University College (CGR)",
    "CIF": "Columbia Icefield (CIF)",
    "CPH": "Carl A. Pollock Hall (CPH)",
    "DC": "William G. Davis Computer Research Centre (DC)",
    "DWE": "Douglas Wright Engineering Building (DWE)",
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
    "MC": "Mathematics & Computer Building (MC)",
    "MHR": "Minota Hagey Residence (MHR)",
    "ML": "Modern Languages (ML)",
    "OPT": "School of Optometry and Vision Science (OPT)",
    "PAC": "Physical Activities Complex (PAC)",
    "PAS": "Psychology, Anthropology, Sociology (PAS)",
    "PHY": "Physics (PHY)",
    "QNC": "Mike & Ophelia Lazaridis Quantum-Nano Centre (QNC)",
    "RCH": "Ron Eydt Village (RCH)",
    "REN": "Renison University College (REN)",
    "STC": "Science Teaching Complex (STC)",
    "TH": "Tatham Centre (TH)",
    "UWP": "University of Waterloo Place (UWP)",
    "V1": "Village 1 (V1)",
    "WEM": "William M. Tatham Centre (WEM)",
}

def parse_schedule(text: str) -> List[Dict[str, Any]]:
    courses = []
    
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
        course_name = match.group(2).strip()
        
        start_idx = match.end()
        end_idx = course_matches[i+1].start() if i + 1 < len(course_matches) else len(text)
        course_block = text[start_idx:end_idx]
        
        # find classes in course block
        class_matches = list(class_header_re.finditer(course_block))
        parsed_classes = []
        
        for j, c_match in enumerate(class_matches):
            class_num = c_match.group(1)
            section = c_match.group(2)
            component = c_match.group(3)
            
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
                location = "TBA"
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
                        location = parts[0]
                        if len(parts) > 1:
                            instructor = ", ".join(parts[1:])
                        else:
                            instructor = "TBA"

                # resolve building name
                loc_parts = location.split()
                if loc_parts:
                    bldg_code = loc_parts[0]
                    if bldg_code in BUILDING_MAP:
                        full_name = BUILDING_MAP[bldg_code]
                        location = f"{full_name} {' '.join(loc_parts[1:])}"

                parsed_classes.append({
                    "class_num": class_num,
                    "section": section,
                    "component": component,
                    "days": current_days,
                    "start_time": start_time,
                    "end_time": end_time,
                    "location": location,
                    "instructor": instructor,
                    "date_start": date_start_str,
                    "date_end": date_end_str
                })
        
        courses.append({
            "code": course_code,
            "name": course_name,
            "classes": parsed_classes
        })

    return courses

def main():
    try:
        with open("src/input.txt", "r") as f:
            content = f.read()
        
        schedule = parse_schedule(content)
        
        # print to stdout for run.sh to potentially capture, or just log
        print(f"parsed {len(schedule)} courses")
        
        with open("src/schedule.json", "w") as f:
            json.dump(schedule, f, indent=2)
        print("saved to src/schedule.json")
            
    except FileNotFoundError:
        print("error: src/input.txt not found.")
    except Exception as e:
        print(f"error parsing schedule: {e}")

if __name__ == "__main__":
    main()
