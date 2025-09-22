# Lineage Build Status

Since I've automated building Lineage for all devices, here's the
current build status for Lineage 22.2. Note that all of the device
specific support for extracting files varies slightly. If the script
can't extract the proprietary files sucessfully, it gets marked as a
failure. Sometimes these look like a simple bug fix, but these
results are based on an unmodified source tree for how.

Using the [extractor](extractor.md) program I can extract all the
files, including the ones where Lineage fails to do so. This seperates
extracting files for analysis instead of building Lineage. Still, this
chart should be useful to anyone wanting to build current Lineage for
their device without fixing the file extraction process.

## File Extraction Status

| Vendor    | Model                | Build          | Extract 22.2   |
|:----------|:---------------------|:---------------|:---------------|
| OnePlus   | Nord 200             | dre            | completes      |
|           | Nord CE2             | oscaro         | completes      |
|           | Nord N10             | billie         |                |
|           | Nord N30             | larry          | completes      |
|           | OnePlus 11 5G        | salami         | completes      |
|           | OnePlus 5            | cheeseburger   | fails          |
|           | OnePlus 5T           | dumpling       |                |
|           | OnePlus 6            | enchilada      | completes      |
|           | OnePlus 6T           | fajita         | completes      |
|           | OnePlus 7            | guacamoleb     | fails          |
|           | OnePlus 7 Pro        | guacamole      | fails          |
|           | OnePlus 7T           | hotdogb        | fails          |
|           | OnePlus 7T Pro       | hotdog         | fails          |
|           | OnePlus 8            | instantnoodle  | completes      |
|           | OnePlus 8 Pro        | instantnoodlep | completes      |
|           | OnePlus 8T           | kebab          | completes      |
|           | OnePlus 9 Pro        | lemonadep      | completes      |
|           | OnePlus 9R           | lemonades      | completes      |
|           | OnePlus 9RT          | martini        | completes      |
|           | Nord N20 5G          | gunnar         | fails          |
|           |                      |                |                |
| Google    | ADT 3                | deadpool       | completes      |
|           | Pixel                | sailfish       | fails          |
|           | Pixel 2XL            | taimen         | fails          |
|           | Pixel 3              | blueline       | completes      |
|           | Pixel 3A XL          | bonito         | completes      |
|           | Pixel 3XL            | crosshatch     | completes      |
|           | Pixel 4              | flame          | completes      |
|           | Pixel 4A             | sunfish        | completes      |
|           | Pixel 4A 5G          | bramble        | completes      |
|           | Pixel 4XL            | coral          | completes      |
|           | Pixel 5              | redfin         | completes      |
|           | Pixel 5A             | barbet         | completes      |
|           | Pixel 6              | oriole         | completes      |
|           | Pixel 6 Pro          | raven          | completes      |
|           | Pixel 6A             | bluejay        | completes      |
|           | Pixel 7              | panther        | completes      |
|           | Pixel 7 Pro          | cheetah        | completes      |
|           | Pixel 7A             | lynx           | fails          |
|           | Pixel 8              | shiba          | completes      |
|           | Pixel 8 Pro          | husky          | completes      |
|           | Pixel 8A             | akita          | completes      |
|           | Pixel 9              | tokay          | completes      |
|           | Pixel 9 Pro          | caiman         | completes      |
|           | Pixel 9 Pro Fold     | comet          | completes      |
|           | Pixel Fold           | felix          | completes      |
|           | Pixel Tablet         | tangorpro      | completes      |
|           | Pixel XL             | marlin         | completes      |
|           | Pixel 2              | walleye        | fails          |
|           |                      |                |                |
| Motorola  | Defy 2021            | bathena        | fails          |
|           | Edge                 | racer          | fails          |
|           | Edge 20              | berlin         | completes      |
|           | Edge 20 Pro          | pstar          | completes      |
|           | Edge 2021            | berlna         | fails          |
|           | Edge 30              | dubai          | fails          |
|           | Edge 30 Fusion       | tundra         | fails          |
|           | Edge 30 Neo          | miami          | fails          |
|           | Edge 30 Ultra        | eqs            | fails          |
|           | Edge 40              | dubai          | fails          |
|           | Edge 40 Pro          | rtwo           | completes      |
|           | Edge S               | nio            | completes      |
|           | Moto G 5G            | kiev           | completes      |
|           | Moto E7 Plus         | guam           | fails          |
|           | Moto G 5G 2024       | fogo           | completes      |
|           | Moto G 5G Plus       | nairo          | fails          |
|           | Moto G Power         | borneo         | completes      |
|           | Moto G10             | capri          | fails          |
|           | Moto G200            | xpeng          | fails          |
|           | Moto G30             | caprip         | fails          |
|           | Moto G32             | devon          | fails          |
|           | Moto G34 5G          | fogos          | fails          |
|           | Moto G42             | hawao          | fails          |
|           | Moto G52             | rhode          | fails          |
|           | Moto G5G Plus        | nairo          | completes      |
|           | Moto G6 Plus         | evert          | fails          |
|           | Moto G7              | river          | fails          |
|           | Moto G7 Power        | ocean          | completes      |
|           | Moto G7P Plus        | lake           | fails          |
|           | Moto G82 5G          | rhodep         | fails          |
|           | Moto G84 5G          | bangkk         | fails          |
|           | Moto G9              | guamp          | fails          |
|           | Moto G9 Power        | cebu           | fails          |
|           | Moto X4              | payton         | fails          |
|           | Motoi Z3             | messi          | fails          |
|           | One Action           | troika         | completes      |
|           | One Vision           | kane           | completes      |
|           | ThinkPhone           | bronco         | completes      |
|           |                      |                |                |
| Xiaomi    | Black Shark          | shark          | fails          |
|           | MI 10                | umi            | fails          |
|           | Mi 10 5G             | monet          |                |
|           | Mi 10 Pro            | cmi            | fails          |
|           | Mi 10 Pro            | cmi            | fails          |
|           | Mi 10S               | thyme          | completes      |
|           | Mi 10T               | apollon        | fails          |
|           | Mi 10T 5G            | gauguin        | fails          |
|           | Mi 11 5G             | lisa           | completes      |
|           | Mi 11 5G             | renoir         | completes      |
|           | Mi 11 Pro            | mars           |                |
|           | Mi 11I               | haydn          | completes      |
|           | Mi 12                | cupid...       | completes      |
|           | Mi 12 Pro            | zeus           | completes      |
|           | Mi 12S               | mayfly         | completes      |
|           | Mi 12S Pro           | unicorn        | completes      |
|           | Mi 12S Ultra         | thor           | completes      |
|           | Mi 12T Pro           | diting         | completes      |
|           | Mi 13                | fuxi           | completes      |
|           | Mi 13 Pro            | nuwa           | completes      |
|           | Mi 5                 | gemini         | fails          |
|           | Mi 5S Plus           | natrium        | fails          |
|           | Mi 6                 | sagit          | fails          |
|           | Mi 8                 | dipper         | fails          |
|           | Mi 8 Explorer        | ursa           | fails          |
|           | Mi 8 Pro             | equuleus       | fails          |
|           | Mi 9SE               | grus           | fails          |
|           | Mi A3                | laurel sprout? | completes      |
|           | Mi CC9               | pyxis          | fails          |
|           | Mi CC9 Meitu         | vela           | fails          |
|           | Mi Fold 2            | zizhan         | completes      |
|           | Mi Mix 2             | chiron         | fails          |
|           | Mi Mix 2S            | polaris        | fails          |
|           | Mi Mix 3             | perseus        | fails          |
|           | Poco 12C             | earth          | completes      |
|           | Poco 3S              | Mi8937         | fails          |
|           | Poco F1              | beryllium      | fails          |
|           | Poco F2 Pro          | lmi            | fails          |
|           | Poco F3              | alioth         | completes      |
|           | Poco F4              | munch          | completes      |
|           | Poco F5              | marble         | completes      |
|           | Poco F5 Pro          | mondrian       | completes      |
|           | Poco M2 Pro          | miatoll        | fails          |
|           | Poco X3 NFC          | surya          | fails          |
|           | Poco X3 Pro          | vayu           | fails          |
|           | RedmI 8              | Mi439          | completes      |
|           | Redmi 10S            | rosemary       | completes      |
|           | Redmi 4A             | Mi8917         | fails          |
|           | Redmi 7              | quill          | completes      |
|           | Redmi 7A             | Mi439          | fails          |
|           | Redmi K20 Mi 9       | davinci        | fails          |
|           | Redmi K60 Pro        | socrates       | completes      |
|           | Redmi Note 10 Pro    | sweet          | fails          |
|           | Redmi Note 7 Pro     | violet         | fails          |
|           | Redmi Note 8         | ginkgo         | fails          |
|           | Redmi Note 9 Pro     | miatoll        | fails          |
|           |                      |                |                |
| Fairphone | FP3                  | FP3            | fails          |
|           | FP5                  | FP5            | completes      |
|           | FP4                  | FP4            | completes      |
|           |                      |                |                |
| Samsung   | Galaxy Tab S5e Wifi  | gts4lvwifi     | fails          |
|           | Galaxy Note 10 5G    | d1x            | fails          |
|           | Galaxy A72           | a72q           | fails          |
|           | Galaxy A52 4G        | a52q           | fails          |
|           | Galaxy Tab S6 LTE    | gta4xl         | fails          |
|           | Galaxy S10           | beyond1lte     | fails          |
|           | Galaxy Tab A7 Wifi   | gta4lwifi      | fails          |
|           | Galaxy A21s          | a21s           | fails          |
|           | Galaxy A71           | a71            | fails          |
|           | Galaxy S10 Plus      | beyond2lte     | fails          |
|           | Galaxy Tab S7 Wifi   | gts7lwifi      | fails          |
|           | Galaxy S10 5G        | beyondx        | fails          |
|           | Galaxy Tab S6 Wifi   | gta4xlwifi     | fails          |
|           | Galaxy TabA 8.0      | gtowifi        | fails          |
|           | Galaxy Tab S7 LTE    | gts7l          | fails          |
|           | Galaxy S20 FE        | r8q            | fails          |
|           | Galaxy F62           | f62            | fails          |
|           | Galaxy Note 10 Plus  | d2s            | fails          |
|           | Galaxy M52 5G        | m52xq          | fails          |
|           | Galaxy TabA 10.4 LTE | gta4l          | fails          |
|           | Galaxy A52s 5G       | a52sxq         | fails          |
|           | Galaxy A73 5G        | a73xq          | fails          |
|           | Galaxy S10e          | beyond0lte     | fails          |
|           | Galaxy Tab S5e LTE   | gts4lv         | fails          |
|           | Galaxy Note 10       | d1             | fails          |
|           |                      |                |                |
| LGE       | G7 ThinQ             | judyln         | completes      |
|           | G8 ThinQ             | alphaplus      | completes      |
|           | V30                  | joan           | fails          |
|           | V35                  | judyp          | completes      |
|           | V40                  | judypn         | completes      |
|           | V50 ThinQ            | flashlmdd      | completes      |
|           |                      |                |                |
| ASUS      | ZenPhone 5Z          | Z01R           | fails          |
|           |                      |                |                |
| Lenovo    | Z6 Pro               | zippo          | fails          |
|           | Z5 Pro GT            | heart          | fails          |
|           |                      |                |                |
| FxTec     | Pro 1X               | pro1x          | completes      |
|           | Pro 1                | pro1           | fails          |
|           |                      |                |                |
| Nvidia    | Jetson Tablet        | porg tab       | fails          |
|           | Jetson TV            | porg           | fails          |
|           | TX1 Tablet           | foster tab     | fails          |
|           | TX1 TV               | foster         | fails          |
|           | TX2 Tablet           | quill tag      | fails          |
|           | TX2 TV               | quill          | fails          |
|           |                      |                |                |
| Essential | PH 1                 | mata           | completes      |
|           |                      |                |                |
| Nothing   | Phone 1              | Spacewar       | completes      |
|           | Phone 2              | Pong           | completes      |
|           |                      |                |                |
| Nokia     | 6.1 2018             | PL2            | fails          |
|           | 7 Plus               | B2N            | fails          |
|           |                      |                |                |
| Sony      | Xperia XA2           | pioneer        | completes      |
|           | Xperia XZ2 Premium   | aurora         | completes      |
|           | Xperia XZ2 Compact   | xz2c           | completes      |
|           | Xperia 5 III         | pdx214         | completes      |
|           | Xperia XA2 Plus      | voyager        | completes      |
|           | Xperia 1 II          | pdx203         | completes      |
|           | Xperia 5 II          | pdx206         | completes      |
|           | Xperia 10 IV         | pdx225         | completes      |
|           | Xperia XA2 Ultra     | discovery      | completes      |
|           | Xperia 5 V           | pdx237         | completes      |
|           | Xperia 10 V          | pdx235         | completes      |
|           | Xperia 10 Plus       | mermaid        | completes      |
|           | Xperia XZ2           | akari          | completes      |
|           | Xperia XZ3           | akatsuki       | completes      |
|           | Xperia 1 V           | pdx234         | completes      |
|           |                      |                |                |
| Solana    | Saga                 | ingot          | completes      |
|           |                      |                |                |
| Shift     | Shift 6MQ            | axolotl        | completes      |
|           |                      |                |                |
| Razer     | Phone                | cheryl         | completes      |
|           | Phone 2              | aura           | completes      |
|           |                      |                |                |
| Nubia     | Z17                  | nx563j         | fails          |
|           | Red Magic Mars       | nx619j         | fails          |
|           | Z18                  | nx606j         | fails          |
|           | Red Magic 5G         | nx659j         | fails          |
|           | Mini 5G              | TP1803         | fails          |
|           |                      |                |                |
| Radxa     | Zero TV              | radxa0         |                |
|           | Zero Tablet          | radxa0 tab     | fails          |
|           | Zero 2 TV            | radxa02        | fails          |
|           | Zero 2 Tablet        | radxa02 tab    | fails          |
|           |                      |                |                |
|           |                      |                |                |
| Realme    | Realme 10 Pro        | luigi          | completes      |
|           | Realme 9 Pro         | oscar          | completes      |
|           |                      |                |                |
| ZTE       | Axon 9 Pro           | akershus       | fails          |
|           |                      |                |                |
| BananaPI  | M5 TV                | m5             | fails          |
|           | M5 Tablet            | m5 tab         | fails          |

## Build Status

__Coming soon!__
