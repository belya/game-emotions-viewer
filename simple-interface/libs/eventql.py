import re
import pandas as pd
import numpy as np


def create_events_dictionary(events):
    events_dict = {}
    
    for event in events:
        for letter in event:
            if letter not in events_dict.values():
                events_dict[event] = letter
                break
        
        if event not in events_dict:        
            assert False, "No such letter"
    
    return events_dict


def get_eventql_source_string(events_df, events_dict):
    parts = events_df['type'].apply(events_dict.get).tolist()
    
    return "".join(parts)


def extract_sub_regex(eventql_string, events_dict):
    events = eventql_string.split('->')
    
    regex_parts = []
    for event in events:
        if not event:
            continue
        letter = events_dict[event]
        regex_parts.append(letter)
    
    return "".join(regex_parts)


def extract_regex(eventql_string, events_dict):
    eventql_string = eventql_string.replace(' ', '')
    head, body_tail = eventql_string.split('[')
    body, tail = body_tail.split(']')
    
    head_regex = extract_sub_regex(head, events_dict)
    body_regex = extract_sub_regex(body, events_dict)
    tail_regex = extract_sub_regex(tail, events_dict)
    
    return f"""
        (?<={head_regex})({body_regex})(?={tail_regex})
    """.strip()


def search_regex_indices(events_df, source_string, regex):
    positions_df = pd.DataFrame(
        [(m.start(0), m.end(0) - 1) for m in re.finditer(regex, source_string)],
        columns=['start', 'end']
    )
    
    start_time = events_df.iloc[
        positions_df['start']
    ]['start'].tolist()

    end_time = events_df.iloc[
        positions_df['end']
    ]['end'].tolist()
    
    fragments_df = pd.DataFrame(
        np.array([start_time, end_time]).T,
        columns=['start', 'end']
    )
    fragments_df['type'] = ''
    
    return fragments_df
