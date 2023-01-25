import requests
import json
import re
import time
from PIL import Image, ImageDraw, ImageFont

start=time.perf_counter()
delay_time=7200

while True:
    card_of_interest="Ice-Fang Coatl"
    url2='https://www.mtgo.com/en/mtgo/decklists'
    event_webpg=requests.get(url2)

    list_start=event_webpg.text.find('<ul class="decklists-list">')+28
    list_end=(event_webpg.text.find('<footer class="site-footer" id="footer">')-44)

    event_string=event_webpg.text[list_start:list_end]

    event_list=re.findall('/en/mtgo/decklist.*\d"', event_string)

    historic_lists=open("event_list.txt","r")
    last_events=historic_lists.read()
    historic_lists.close()

    last_events=last_events.replace('"','" ').split()

    new_events=list(set(event_list)-set(last_events))
    log_file=open("scanning_log.txt", "a")
    if new_events==[]:
        log_file.write(f"No new events at {time.ctime()}\n")
        log_file.close()
    else:
        decks_with_coatl=[]
        log_file.write(f"Found new event(s), checking them at {time.ctime()}\n")
        for event in new_events:
            if "modern" in event or "legacy" in event:
                url='https://www.mtgo.com'+event[:-1]
                resp=requests.get(url)
                event_name=' '.join(event.split('/')[4].split('-')[:-3])
                decks="{"+resp.text[resp.text.find('"decks":'):(resp.text.find('window.MTGO.decklists.roundNames')-6)]
                finishes_dict=json.loads(decks)
                decks_dict=finishes_dict['decks']
                for i in range(len(decks_dict)):
                    current_player=decks_dict[i]["player"]
                    current_decklist={'Player':current_player, 'Event':event_name}
                    current_deck_has_coatl=False
                    for j in range(len(decks_dict[i]['deck'])):
                        if decks_dict[i]['deck'][j]['SB']==True:
                            card_category='Sideboard'
                        else:
                            card_category='Main Deck'
                        card_count=0
                        current_decklist[card_category]={}
                        for k in range(len(decks_dict[i]['deck'][j]['DECK_CARDS'])):
                            card_quantity=decks_dict[i]['deck'][j]['DECK_CARDS'][k]['Quantity']
                            try:
                                card_type=decks_dict[i]['deck'][j]['DECK_CARDS'][k]['CARD_ATTRIBUTES']['Type']
                            except:
                                card_type='Split'
                            card_name=decks_dict[i]['deck'][j]['DECK_CARDS'][k]['CARD_ATTRIBUTES']['NAME']
                            current_decklist[card_category][card_name]=[card_type, card_quantity]
                            if card_name==card_of_interest:
                                current_deck_has_coatl=True
                    if current_deck_has_coatl:
                        log_file.write(f"Found a new coatl deck! Adding it to the list at {time.ctime()}\n")
                        decks_with_coatl.append(current_decklist)
        # historic_lists=open("event_list.txt","w")
        # historic_lists.writelines(event_list)
        # historic_lists.close()
        if decks_with_coatl==[]:
            log_file.write(f"No new coatls in this event, sorry. TS: {time.ctime()}\n")
            log_file.close()

    organized_decks=[]
    for deck in decks_with_coatl:
        current_decklist_created=\
            {'Player':deck['Player'], 'Event':deck['Event'],\
            'Main Deck':\
                {'Creatures':{}, 'Planeswalkers' :{}, 'Instants': {}, 'Sorceries':{}, 'Artifacts':{}, 'Enchantments':{}, 'Lands':{}},\
            'Sideboard': []}
        for card in deck['Main Deck']:
            try:
                if deck['Main Deck'][card][0]=='Creature':
                    current_decklist_created['Main Deck']['Creatures'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Planeswalker':
                    current_decklist_created['Main Deck']['Planeswalkers'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Instant':
                    current_decklist_created['Main Deck']['Instants'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Sorcery':
                    current_decklist_created['Main Deck']['Sorceries'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Artifact':
                    current_decklist_created['Main Deck']['Artifacts'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Enchantment':
                    current_decklist_created['Main Deck']['Enchantments'][card]=deck['Main Deck'][card][1]
                if deck['Main Deck'][card][0]=='Land':
                    current_decklist_created['Main Deck']['Lands'][card]=deck['Main Deck'][card][1]
            except:
                print("empty list")
        current_decklist_created['Sideboard']=deck['Sideboard']
        organized_decks.append(current_decklist_created)
    
    for deck in organized_decks:
        print(deck)
        deck_name=(deck['Event']+deck['Player']).replace(" ","")
        deck_background=Image.open('deck_background.png')
        deck_image=ImageDraw.Draw(deck_background)
        big_font=ImageFont.truetype('OpenSans-Regular.ttf', 20)
        mid_font=ImageFont.truetype('OpenSans-Semibold.ttf', 13)
        small_font=ImageFont.truetype('OpenSans-Regular.ttf', 12)
        league_name=f'Event: {deck["Event"].title()}'
        deck_image.text((90,60), league_name, font=big_font, fill=(0, 0, 0))
        deck_image.text((570,60), ("Pilot: "+deck['Player']), font=big_font, fill=(0, 0, 0))
        
        print("\n"+deck['Event'].upper()+"\n")
        print(deck['Player'],"\n")
        print("Main deck: ")
        row_count=1.7
        for category in deck['Main Deck']:
            if (deck['Main Deck'][category] and category!='Lands'):
                print("\n"+category+":")
                deck_image.text((90,70+20*row_count), (category+":"), font=mid_font, fill=(0, 0, 0))
                row_count+=1
                for card in deck['Main Deck'][category]:
                    print(deck['Main Deck'][category][card], card)
                    deck_image.text((90,70+20*row_count), (str(deck['Main Deck'][category][card])+" "+card), font=small_font, fill=(0, 0, 0))
                    row_count+=1
                row_count+=0.2
            elif (deck['Main Deck'][category] and category=='Lands'):
                row_count=1.7
                print("\n"+category+":")
                deck_image.text((370,70+20*row_count), (category+":"), font=mid_font, fill=(0, 0, 0))
                row_count+=1
                for card in deck['Main Deck'][category]:
                    print(deck['Main Deck'][category][card], card)
                    deck_image.text((370,70+20*row_count), (str(deck['Main Deck'][category][card])+" "+card), font=small_font, fill=(0, 0, 0))
                    row_count+=1
                row_count+=0.2
        row_count=1.7
        deck_image.text((600,70+20*row_count), ("Sideboard:"), font=mid_font, fill=(0, 0, 0))
        row_count+=1
        print("\nSideboard: ")
        for card in deck['Sideboard']:
            current_card=(str(deck['Sideboard'][card][1])+" "+card)
            print(deck['Sideboard'][card][1], card)
            deck_image.text((600,70+20*row_count), current_card, font=small_font, fill=(0, 0, 0))
            row_count+=1
        deck_background.save(f'C:\python projects\coatl_enjoyer\deck_images/{deck_name}.png')
    end_time=time.perf_counter()
    print(end_time-start)
    time.sleep(delay_time)