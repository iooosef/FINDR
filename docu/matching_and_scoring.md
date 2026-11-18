# How Matching & Scoring Works

Quick rundown of how FINDR matches lost items with found items and how the score works.

---

## 1. Flowchart

```mermaid
flowchart TD
    Start["New Report Submitted<br>(Missing or Found)"] --> GetCandidates["Check active tickets in DB"]
    
    GetCandidates --> CheckCat{"Same Category?"}
    CheckCat -- "No" --> NoMatch["No Match (Score = 0.0)<br>Stops right here"]
    CheckCat -- "Yes" --> BaseScore["Base score = 0.40"]

    BaseScore --> CheckColor{"Same Color?"}
    CheckColor -- "Yes" --> ColorPts["Add +0.20"]
    CheckColor -- "No" --> CheckBrand{"Same Brand?"}
    ColorPts --> CheckBrand

    CheckBrand -- "Yes" --> BrandPts["Add +0.20"]
    CheckBrand -- "No" --> CheckWords{"Words overlap in name/desc?"}
    BrandPts --> CheckWords

    CheckWords -- "Yes" --> WordPts["Add up to +0.20"]
    CheckWords -- "No" --> GotSecondary{"Matched at least 1 extra thing?<br>(Color, Brand, or Words)"}
    WordPts --> GotSecondary

    GotSecondary -- "No" --> DropIt["No Match (Score = 0.0)<br>Category alone isn't enough"]
    GotSecondary -- "Yes" --> ItsAMatch["It's a Match!<br>Score: 0.50 to 1.00"]

    ItsAMatch --> SaveMatch["Save to 'matches' table (pending)"]
    SaveMatch --> WhoMatched{"How many students matched this found item?"}
    
    WhoMatched -- "Just 1 student" --> Single["Notify student to visit office.<br>Item stays 'unclaimed'."]
    WhoMatched -- "2 or more students" --> Conflict["Conflict! Set item to 'pending_verification'.<br>Notify all matched students & staff."]

    Single --> Office["Student visits L&F office at Balbago"]
    Conflict --> Office

    Office --> StaffDecides{"Staff inspects item in person"}
    StaffDecides -- "Verified owner" --> Winner["Item marked 'claimed'<br>Student report marked 'resolved'"]
    StaffDecides -- "Other students" --> Loser["Their ticket goes back to 'open'<br>Can match future items"]
```

---

## 2. Points Breakdown

Total score is between **0.0** and **1.0** (0% to 100%).

| What it checks | Points | Notes |
|---|---|---|
| **Category** | **+0.40** | **Must match.** If this fails, everything stops and score is `0.0`. An umbrella won't match a phone. |
| **Color** | **+0.20** | Simple text check (e.g., "black" matches "matte black"). |
| **Brand** | **+0.20** | Simple text check (e.g., "casio" matches "Casio fx-991"). |
| **Keywords** | **up to +0.20** | Compares words in item name and description (ignores words like "the", "a", "lost"). |

### The main rule
To actually count as a match:
- Must have the **same Category**
- **PLUS at least 1 other thing** (Color, Brand, or Keywords)

If only the category matches and nothing else, it gets tossed out (score = 0.0). We don't want every lost ID matching every found ID.

---

## 3. Why is there a score?

- **Sorting**: If staff has 4 black umbrellas in the office, the one with 95% (same brand + model) shows up first before the 60% ones.
- **Tells you how close it is**:
  - `0.60` = kinda close (same category + color, unknown brand).
  - `0.95` = almost definitely it (category, color, brand, and model words all match).
- **Helps staff verify**: Staff doesn't have to read every single ticket. The highest score is probably the right one.

---

## 4. Conflicts (Multiple people matching 1 item)

If 2 students lost a black Casio calculator and staff logs 1 black Casio calculator:
1. Found item changes to `pending_verification`.
2. Both students get a notification to visit the office.
3. Staff checks the physical item (stickers, serials, scratches, proof).
4. Staff hits **Verify** on the real owner:
   - Winner gets marked `resolved` and item is `claimed`.
   - The other student's ticket gets set back to `open` so it can match future found items.

---

## 5. Privacy note

Students **never** see photos or where the item was found.
Their notification just says:
> *"We found a possible match for your missing [Item]. Please visit the Lost and Found Office for in-person verification."*

This stops people from looking at the details and pretending it's theirs.
