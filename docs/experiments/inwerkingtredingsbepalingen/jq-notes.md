# Experiment Inwerkingtredingsbepalingen

Some notes on how to extract specific data from the results files using jq and other common Linux tools.

Use the `.json`-file created by `./manage.py experiment_inwerkingtredingsbepalingen` as your input.

## All unique inwerkingtredingsbepalingen including a count

Command:
```
$ cat experiment-inwerkingtredingsbepalingen-task-{date}.json | jq '.[]["predictions"][]["result"][]["value"]["text"]' | sed -E 's/(\\t)+|(\\r\\n)+|\\n +/ /g' | sed -E 's/ +/ /g' | sort | uniq -c | sort -n > unieke_gevonden_inwerkingtredingsbepalingen.txt
```

Example output:

```
$ tail -n 5 unieke_gevonden_inwerkingtredingsbepalingen.txt
    373 "Deze wet treedt in werking met ingang van 1 januari van het onderhavige begrotingsjaar. Indien het Staatsblad waarin deze wet wordt geplaatst, wordt uitgegeven op of na deze datum van 1 januari, treedt zij in werking met ingang van de dag na de datum van uitgifte van dat Staatsblad en werkt zij terug tot en met 1 januari."
    391 "Deze wet treedt in werking op een bij koninklijk besluit te bepalen tijdstip, dat voor de verschillende artikelen of onderdelen daarvan verschillend kan worden vastgesteld."
    586 "Deze wet treedt in werking met ingang van de dag na de datum van uitgifte van het Staatsblad waarin zij wordt geplaatst."
    671 "Deze wet treedt in werking met ingang van de dag na de datum van uitgifte van het Staatsblad waarin zij wordt geplaatst en werkt terug tot en met 31 december van het onderhavige begrotingsjaar."
   1036 "Deze wet treedt in werking op een bij koninklijk besluit te bepalen tijdstip."
```

## Text and labels with stb-id

Command:
```
$ cat experiment-inwerkingtredingsbepalingen-task-{date}.json | jq '[.[] | { stbid: .["data"]["stb-id"] , pred: [.["predictions"][]["result"][]["value"] | {text: .text, label: .labels[0] }] }]' > gevonden_inwerkingtredingsbepalingen_met_id.json
```

Example output:

```
$ cat gevonden_inwerkingtredingsbepalingen_met_id.json | jq '.[0]'
{
  "stbid": "stb-2025-11",
  "pred": [
    {
      "text": "Deze wet treedt in werking met ingang van de dag na de datum van uitgifte van het\n                  Staatsblad waarin zij wordt geplaatst en werkt terug tot en met 17 september 2024.",
      "label": "Inwerkingtredingsbepaling zonder delegatie"
    }
  ]
}
```