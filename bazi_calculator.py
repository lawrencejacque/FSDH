# bazi_calculator.py
from datetime import datetime, timedelta
import math

# Make sure lunar_python is installed: pip install lunar_python
from lunar_python import Solar, Lunar

class BaziCalculator:
    def __init__(self):
        # Element meanings for English interpretation
        self.element_meanings = {
            "木": {"name": "Wood", "traits": "Growth, creativity, expansion, leadership, and flexibility.", "advice": "You are visionary and ambitious. Stay grounded to avoid overextending."},
            "火": {"name": "Fire", "traits": "Passion, energy, motivation, inspiration, and visibility.", "advice": "You are charismatic and expressive. Balance intensity with patience."},
            "土": {"name": "Earth", "traits": "Stability, reliability, nurturing, practicality, and organization.", "advice": "You are dependable and thoughtful. Avoid being overly cautious or stagnant."},
            "金": {"name": "Metal", "traits": "Discipline, strength, precision, logic, and determination.", "advice": "You are principled and strong-willed. Loosen rigidity with empathy."},
            "水": {"name": "Water", "traits": "Wisdom, intuition, adaptability, and communication.", "advice": "You are reflective and insightful. Avoid overthinking or hesitation."}
        }
    # ------------------------------
    # Civil time conversion
    # From 1950 until 1981, Singapore’s civil time was UTC+7:30, not +8:00. On 1 Jan 1982, Singapore advanced clocks by 30 minutes, switching to UTC+8:00 permanently.
    # ------------------------------
    def _get_singapore_tz_offset_hours_1950_onwards(dt: datetime) -> float:
    # ------------------------------
    # Historical Singapore UTC offset for civil time, 1950+.
    # Before 1982-01-01: UTC+7:30
    # From 1982-01-01 onwards: UTC+8:00
    # ------------------------------
    cutoff = datetime(1982, 1, 1, 0, 0)
    if dt < cutoff:
        return 7.5  # UTC+07:30 (pre-1982 Singapore)
    else:
        return 8.0  # UTC+08:00 (modern Singapore Time)
        
    # ------------------------------
    # True solar time conversion
    # ------------------------------
    def to_true_solar_time(self, year, month, day, hour, minute, longitude: float, tz_offset: float):
    # ------------------------------
    # Convert local civil time to approximate true solar time based on longitude.
    # longitude: degrees East (east positive, west negative)
    # tz_offset: hours offset from UTC (e.g. Singapore = 8)
    # Returns a datetime (local true solar time).
    # Note: This uses longitude/time-zone meridian offset only (adequate for hour pillar).
    # ------------------------------
        standard_longitude = tz_offset * 15.0
        diff_hours = (longitude - standard_longitude) / 15.0
        delta = timedelta(hours=diff_hours)
        civil_time = datetime(year, month, day, hour, minute)
        solar_time = civil_time + delta
        return solar_time

    # ------------------------------
    # Main calculation
    # ------------------------------
    def calculate_bazi(self, year, month, day, hour, minute, longitude: float = 103.8, tz_offset: float | None = None):
        
        #Calculate BaZi (four pillars) and five-element analysis.
        #longitude: degrees east (Singapore ≈ 103.8). tz_offset: hours from UTC.
        #Returns a dict containing pillars, five-element scores, percentages, ranking,
        #weak elements, strategies, classification, and English interpretation.
        
        civil_dt = datetime(year, month, day, hour, minute)

        if tz_offset is None:
            tz_offset = _get_singapore_tz_offset_hours_1950_onwards(civil_dt)
            
        # 1) Convert to true solar time according to longitude/timezone
        solar_time = self.to_true_solar_time(year, month, day, hour, minute, longitude, tz_offset)

        # 2) Use lunar_python Solar -> Lunar -> EightChar for accurate GanZhi
        solar = Solar.fromYmdHms(solar_time.year, solar_time.month, solar_time.day, solar_time.hour, solar_time.minute, 0)
        lunar = solar.getLunar()
        eight_char = lunar.getEightChar()

        # eight_char.getYear() returns e.g. "甲子", getMonth(), getDay(), getTime()
        year_pillar = eight_char.getYear()
        month_pillar = eight_char.getMonth()
        day_pillar = eight_char.getDay()
        hour_pillar = eight_char.getTime()

        pillars = {
            "year_pillar": year_pillar,
            "month_pillar": month_pillar,
            "day_pillar": day_pillar,
            "hour_pillar": hour_pillar,
            "adjusted_to_true_solar_time": solar_time.strftime("%Y-%m-%d %H:%M:%S"),
            "longitude": longitude,
            "tz_offset": tz_offset
        }

        # 3) Count five-elements from stems & branches
        # We'll break each pillar into stem+branch chars, then map to element
        gan_element_map = {"甲": "木", "乙": "木", "丙": "火", "丁": "火", "戊": "土", "己": "土", "庚": "金", "辛": "金", "壬": "水", "癸": "水"}
        zhi_element_map = {"子": "水", "丑": "土", "寅": "木", "卯": "木", "辰": "土", "巳": "火", "午": "火", "未": "土", "申": "金", "酉": "金", "戌": "土", "亥": "水"}

        # Collect characters: stems and branches of each pillar
        # Each pillar string is usually 2 chars e.g. "甲子" -> stem '甲', branch '子'
        chars = []
        for p in (year_pillar, month_pillar, day_pillar, hour_pillar):
            if isinstance(p, str) and len(p) >= 2:
                chars.append(p[0])   # stem
                chars.append(p[1])   # branch

        scores = {"木": 0, "火": 0, "土": 0, "金": 0, "水": 0}
        for ch in chars:
            if ch in gan_element_map:
                scores[gan_element_map[ch]] += 1
            elif ch in zhi_element_map:
                scores[zhi_element_map[ch]] += 1
            else:
                # ignore unknown char (defensive)
                pass

        # 4) Ranking, percentages, missing elements, strategies, classification, interpretation
        ranked, missing, strategies, classification, interpretation = self.rank_and_interpret(scores)

        return {
            "bazi": pillars,
            "classification": classification,
            "five_elements_scores": scores,
            "ranked_elements": ranked,
            "weak_elements": missing,
            "balance_strategies": strategies,
            "interpretation": interpretation
        }

    # ------------------------------
    # Ranking & interpretation helpers
    # ------------------------------
    def rank_and_interpret(self, scores):
        # ranked list (element, score)
        ranked_elements = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        total = sum(scores.values())
        # percentages normalized for charting
        percentages = {k: round((v / total) * 100, 2) if total > 0 else 0.0 for k, v in scores.items()}

        # missing/weak elements threshold (relative)
        average = total / 5 if total > 0 else 0
        missing_elements = [e for e, v in ranked_elements if v <= math.floor(average * 0.6)]

        element_relationships = {
            '金': {'generates': '水', 'controls': '木', 'generated_by': '土', 'controlled_by': '火'},
            '木': {'generates': '火', 'controls': '土', 'generated_by': '水', 'controlled_by': '金'},
            '水': {'generates': '木', 'controls': '火', 'generated_by': '金', 'controlled_by': '土'},
            '火': {'generates': '土', 'controls': '金', 'generated_by': '木', 'controlled_by': '水'},
            '土': {'generates': '金', 'controls': '水', 'generated_by': '火', 'controlled_by': '木'}
        }

        strategies = self.balance_elements(scores, missing_elements, element_relationships)
        classification = self.classify_balance(percentages)
        interpretation = self.interpret_elements(classification)

        ranked_output = [{"element": e, "score": s, "percentage": percentages.get(e, 0.0)} for e, s in ranked_elements]
        return ranked_output, missing_elements, strategies, classification, interpretation

    def balance_elements(self, scores, missing_elements, element_relationships):
        strategies = []
        for element in missing_elements:
            if element not in element_relationships:
                continue
            gen = element_relationships[element]['generated_by']
            if scores.get(gen, 0) >= 2:
                strategies.append(f"Strengthen {element} by enhancing {gen} ({gen}生{element})")
            else:
                strategies.append(f"Directly strengthen {element} through {element_relationships[element]['generates']} energy")
            ctrl = element_relationships[element]['controlled_by']
            strategies.append(f"Reduce excess influence from {ctrl} if too strong ({ctrl}克{element})")
        return strategies

    def classify_balance(self, percentages):
        # percentages is a dict of element -> percent (0-100)
        dominant = max(percentages, key=percentages.get)
        weakest = min(percentages, key=percentages.get)
        dom_pct = percentages[dominant]
        weak_pct = percentages[weakest]

        if dom_pct >= 30:
            summary = f"{dominant}-dominant chart ({dominant}旺格局)"
        elif weak_pct <= 10:
            summary = f"{weakest}-weak chart ({weakest}弱格局)"
        elif all(15 <= p <= 25 for p in percentages.values()):
            summary = "Balanced chart (五行均衡)"
        else:
            summary = "Mixed balance chart (中庸格局)"

        return {
            "percentages": percentages,
            "dominant": dominant,
            "weakest": weakest,
            "summary": summary
        }

    def interpret_elements(self, classification):
        dominant = classification["dominant"]
        weakest = classification["weakest"]
        dom_meaning = self.element_meanings.get(dominant, {})
        weak_meaning = self.element_meanings.get(weakest, {})

        return {
            "dominant_element": {
                "element": dominant,
                "english_name": dom_meaning.get("name", ""),
                "traits": dom_meaning.get("traits", ""),
                "advice": dom_meaning.get("advice", "")
            },
            "weakest_element": {
                "element": weakest,
                "english_name": weak_meaning.get("name", ""),
                "traits": weak_meaning.get("traits", ""),
                "advice": f"You need more {weak_meaning.get('name','')} energy. {weak_meaning.get('advice','')}"
            }
        }

# Convenience function
def calculate_bazi(year, month, day, hour, minute, longitude: float = 103.8, tz_offset: float = 8.0):
    calc = BaziCalculator()
    return calc.calculate_bazi(year, month, day, hour, minute, longitude, tz_offset)


