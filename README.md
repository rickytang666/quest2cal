<div align="center">
    <h1>Quest2Cal</h1>
    <p><a href="https://quest.pecs.uwaterloo.ca/psp/SS/ACADEMIC/SA/?cmd=login&languageCd=ENG">UWaterloo Quest</a> class schedule to <code>.ics</code> file. Instantly.</p>
</div>

---

## Usage

1.  Copy your schedule from Quest (List View).
2.  Paste it into `src/input.txt`.
3.  Run the script:

    ```bash
    ./run.sh
    ```

    (Optional arguments):

    `--lower` for lowercase names and notes
    `--test` for JSON output as well

4.  Find your schedule in `outputs/schedule.ics`.

Note: Quest2Cal will only output classes (lectures, labs, tutorials, seminars, etc.), not exams.

## Dependencies

- Python 3
- `ics` library (installed automatically by `run.sh`)

## How it works

The script uses regex to parse the raw text hierarchy:

1.  **Course**: `[CODE] - [NAME]` matches course blocks.
2.  **Class**: `[ClassNum] [Section] [Component]` matches class sections within a course.
3.  **Slot**: `[Date Range]` anchors each schedule slot.
    - Backtracks from the date range to find `Instructor`, `Location`, and `Time/Days`.
    - Maps building codes (e.g., `STC`) to full names (e.g., `Science Teaching Complex`).
4.  **Recurrence**:
    - Instead of using standard iCal `RRULE`, the script "flattens" recurrence into individual events for every single class instance.
    - This ensures `America/Toronto` timezone is applied correctly to each event and maximizes compatibility with Google Calendar/Apple Calendar.
