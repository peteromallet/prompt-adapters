# Experiment 006 — 5-probe manual review doc

Each probe shows the own reference (that the adapter was conditioned on), the swap reference (different author/register, same instruction), the instruction given, and 4 variant generations.

**Your call on each probe**: does "adapter" output actually reflect the own-reference style? Does "adapter_swap" reflect the swap-reference style? Is either meaningfully different from "prompted_baseline" (prompting-only) and "no_ref" (no conditioning at all)?

---

## probe_00 — instruction:

> Examine the military principle that excessive valor in defending an indefensible position constitutes a punishable vice requiring disciplinary examples.

### Own reference  (michel_de_montaigne, essay) — first 600 chars

> OF A MONSTROUS CHILD  This story shall go by itself; for I will leave it to physicians to discourse of. Two days ago I saw a child that two men and a nurse, who said they were the father, the uncle, and the aunt of it, carried about to get money by showing it, by reason it was so strange a creature. It was, as to all the rest, of a common form, and could stand upon its feet; could go and gabble much like other children of the same age; it had never as yet taken any other nourishment but from the nurse’s breasts, and what, in my presence, they tried to put into the mouth of it, it only chewed a

### Swap reference  (matthew_arnold, poetry) — first 600 chars

> LECTURE XVII.  RESUME OF DOCTRINE.  Review of the doctrine contained in these lectures, and the three orders of facts on which this doctrine rests, with the relation of each one of them to the modern school that has recognized and developed it, but almost always exaggerated it.--Experience and empiricism.--Reason and idealism.--Sentiment and mysticism.--Theodicea. Defects of different known systems.--The process that conducts to true theodicea, and the character of certainty and reality that this process gives to it.

### **adapter** (conditioned on own ref: michel_de_montaigne)

> _Gallant unto death_, &c.  The truth is, the maxim of Hannibal, "It is better to win one than to lose two," is a maxim of war, and not of valor. The soldier who is ordered to a post of danger, and who, when he is there, acts the part of a hero, is a good soldier, but not a valiant man. A soldier who is ordered to a post of danger, and who, when he is there, acts the part of a coward, is a bad soldier, but not a valueless

### **adapter_swap** (conditioned on swap ref: matthew_arnold)

> III  Heller's specialty was Field Service Regulations, 1857, page 237:  "It is a reproach to arms to be forced to a position from which it is practicable to extricate itself; and it is a still greater one to be thus constrained by the superior force of the enemy. To be thus compelled to a position from which extrication is practicable, is calculated to bring discredit on the troops, and to render them obnoxious to the imputation of cowardice; and it is the duty of every 

### **prompted_baseline** (no adapter, just prompt with own-style hint)

> The military principle that excessive valor in defending an indefensible position constitutes a punishable vice requiring disciplinary examples is a complex and nuanced one. While valor and courage are highly esteemed virtues in the military context, there are instances where such valor can be considered a vice, particularly when it leads to actions that are not only futile but also potentially harmful to the overall mission or objectives of the military unit.  The concept of valor in the military is deeply rooted in the traditions of honor, duty, and sacrifice. Valor is often associated with 

### **no_ref** (base model, no conditioning, no style hint)

> The principle of excessive valor in defending an indefensible position is a military principle that emphasizes the importance of defending a position to the last man, even if it means sacrificing the lives of soldiers. This principle is often associated with the concept of "fighting to the last man" or "fighting to the death." The idea behind this principle is that soldiers should be willing to sacrifice their lives for the sake of their comrades and the cause they are fighting for. However, this principle can also be seen as a form of excessive valor, as it can lead to unnecessary casualties 

---

## probe_02 — instruction:

> Examine the social protocols and courtesies governing the reception of distinguished visitors, and evaluate their practical merit against personal convenience.

### Own reference  (michel_de_montaigne, essay) — first 600 chars

> OF A MONSTROUS CHILD  This story shall go by itself; for I will leave it to physicians to discourse of. Two days ago I saw a child that two men and a nurse, who said they were the father, the uncle, and the aunt of it, carried about to get money by showing it, by reason it was so strange a creature. It was, as to all the rest, of a common form, and could stand upon its feet; could go and gabble much like other children of the same age; it had never as yet taken any other nourishment but from the nurse’s breasts, and what, in my presence, they tried to put into the mouth of it, it only chewed a

### Swap reference  (matthew_arnold, poetry) — first 600 chars

> LECTURE XVII.  RESUME OF DOCTRINE.  Review of the doctrine contained in these lectures, and the three orders of facts on which this doctrine rests, with the relation of each one of them to the modern school that has recognized and developed it, but almost always exaggerated it.--Experience and empiricism.--Reason and idealism.--Sentiment and mysticism.--Theodicea. Defects of different known systems.--The process that conducts to true theodicea, and the character of certainty and reality that this process gives to it.

### **adapter** (conditioned on own ref: michel_de_montaigne)

> _Gratulation_, or the custom of expressing pleasure at the arrival of a guest, is general in England, France, and Italy. The English and French have their _salutations_, or short speeches of welcome; the Italians their _benedizioni_, or long blessings. The Spaniard, the German, and the Pole have their _congratulations_ peculiar to each country.  A _benediction_ is a long speech of welcome, made by the host to his guest, in which he expresses his pleasure at seeing him, and his hope 

### **adapter_swap** (conditioned on swap ref: matthew_arnold)

> III  HOGG AT BRAYTON's  _Sl_ any one of us had been asked to dine with Lord Glenarvet's _s_ eldest son, a year or two before, we should certainly have _s_ thanked him with alacrity. But now, to be asked to dine with him _s_ seemed to us a trial too harassing to be borne. To be asked to _s_ dine with Lord Glenarvet's eldest son, and to be obliged to make _s_ way through the mob of his fashionable

### **prompted_baseline** (no adapter, just prompt with own-style hint)

> The social protocols and courtesies governing the reception of distinguished visitors are designed to ensure a respectful and dignified interaction between the host and the guest. These protocols are rooted in the principles of hospitality and respect for the guest's status and identity.  The practical merit of these protocols lies in their ability to create a harmonious and comfortable environment for both the host and the guest. By adhering to these protocols, the host can demonstrate their respect and appreciation for the guest's presence, which can lead to a more enjoyable and memorable ex

### **no_ref** (base model, no conditioning, no style hint)

> Examine the social protocols and courtesies governing the reception of distinguished visitors, and evaluate their practical merit against personal convenience. Examine the social protocols and courtesies governing the reception of distinguished visitors, and evaluate their practical merit against personal convenience. Examine the social protocols and courtesies governing the reception of distinguished visitors, and evaluate their practical merit against personal convenience. Examine the social protocols and courtesies governing the reception of distinguished visitors, and evaluate their practi

---

## probe_04 — instruction:

> Examine how human self-ignorance and insatiable desire prevent us from achieving lasting contentment with what we possess.

### Own reference  (michel_de_montaigne, essay) — first 600 chars

> OF A MONSTROUS CHILD  This story shall go by itself; for I will leave it to physicians to discourse of. Two days ago I saw a child that two men and a nurse, who said they were the father, the uncle, and the aunt of it, carried about to get money by showing it, by reason it was so strange a creature. It was, as to all the rest, of a common form, and could stand upon its feet; could go and gabble much like other children of the same age; it had never as yet taken any other nourishment but from the nurse’s breasts, and what, in my presence, they tried to put into the mouth of it, it only chewed a

### Swap reference  (matthew_arnold, poetry) — first 600 chars

> LECTURE XVII.  RESUME OF DOCTRINE.  Review of the doctrine contained in these lectures, and the three orders of facts on which this doctrine rests, with the relation of each one of them to the modern school that has recognized and developed it, but almost always exaggerated it.--Experience and empiricism.--Reason and idealism.--Sentiment and mysticism.--Theodicea. Defects of different known systems.--The process that conducts to true theodicea, and the character of certainty and reality that this process gives to it.

### **adapter** (conditioned on own ref: michel_de_montaigne)

> _THOU art all this mortal wo is, And I no more than thou; In wisdom, in command, in might, And in all things whatsoever, Thou art my equal: being so, What should I further ask of thee? The truth is, I do but err, And think I want that which I have.

### **adapter_swap** (conditioned on swap ref: matthew_arnold)

> SEPOLSKY-,_F_.—_The Life of Re_food_,_p. 177.  To the same effect are the words of Bayle:—  '_However, we should not be too much elated at the prospect of possessing any property. For, if we consider the nature of things, we shall find that our contentment with our present lot will always be temptingly short-lived. The very things which we now possess will, in the course of time, become the objects of our desire. Our present possessions will become

### **prompted_baseline** (no adapter, just prompt with own-style hint)

> The story of the monstrous child is a reminder of the limits of human knowledge and the dangers of seeking to control nature. The child's double body and multiple limbs are a symbol of the complexity and interconnectedness of the natural world, which humans often try to simplify and control. The herdsman without genital parts is a reminder of the diversity and complexity of human bodies and the ways in which they can function without the traditional signs of masculinity and femininity. The story also highlights the dangers of seeking to control nature, as the herdsman's condition is a result o

### **no_ref** (base model, no conditioning, no style hint)

> The Buddha taught that the human mind is a restless monkey, and that the only way to achieve lasting contentment is to tame the monkey. The Buddha taught that the human mind is a restless monkey, and that the only way to achieve lasting contentment is to tame the monkey. The Buddha taught that the human mind is a restless monkey, and that the only way to achieve lasting contentment is to tame the monkey. The Buddha taught that the human mind is a restless monkey, and that the only way to achieve lasting contentment is to tame the monkey. The Buddha taught that the human mind is

---

## probe_06 — instruction:

> Document the comprehensive scope and authoritative value of a historical reference work cataloging a nation's affairs and global events for a specific year.

### Own reference  (matthew_arnold, poetry) — first 600 chars

> LECTURE XVII.  RESUME OF DOCTRINE.  Review of the doctrine contained in these lectures, and the three orders of facts on which this doctrine rests, with the relation of each one of them to the modern school that has recognized and developed it, but almost always exaggerated it.--Experience and empiricism.--Reason and idealism.--Sentiment and mysticism.--Theodicea. Defects of different known systems.--The process that conducts to true theodicea, and the character of certainty and reality that this process gives to it.

### Swap reference  (sara_teasdale, poetry) — first 600 chars

> On every vessel that starts for Newfoundland from sixty to seventy men embark. Of this number twelve are sailors: the balance consists of villagers snatched from their work in the fields, who, engaged as day laborers for the preparation of fish, remain strangers to the rigging, and have nothing that is marine about them except their feet and stomach. Nevertheless, these men figure on the rolls of the naval inscription, and there perpetuate a deception. When there is occasion to defend the institution of premiums, these are cited in its favor; they swell the numbers and contribute to success.

### **adapter** (conditioned on own ref: matthew_arnold)

> To _The Year 1897_!—being the memorable year of the Spanish-American War, 1897-1898, and the celebration of the hundredth anniversary of the Monroe Doctrine, 1897-1898.  Colonel Elliot's _Year_ is a mine of information for the general reader, and will prove of especial value to the student and the general reader.

### **adapter_swap** (conditioned on swap ref: sara_teasdale)

> The "Catalogue of Spanish Books Printed Before 1701" is a monument of the learned industry of the compilers, and of the skill of the printers. It is the best of its kind, and the only one of its kind.  A. "It is the best of its kind, and the only one of its kind."  B. "The best of its kind, and the only one of its kind."  C. "The best of its kind, and the only one of its kind."  D. "The best of its kind, and the only

### **prompted_baseline** (no adapter, just prompt with own-style hint)

> The comprehensive scope and authoritative value of a historical reference work cataloging a nation's affairs and global events for a specific year is significant. It provides a detailed account of the events that occurred during that year, including political, social, economic, and cultural developments. This information is essential for understanding the context in which events unfolded and for analyzing their impact on society.  The reference work serves as a reliable source of information, as it is compiled by experts in the field and undergoes rigorous fact-checking and verification proces

### **no_ref** (base model, no conditioning, no style hint)

> This book is a comprehensive reference work on the history of the United States in 1999. It provides a detailed account of the major events, trends, and developments that shaped the country during that year. The book covers a wide range of topics, including politics, economics, culture, and social issues. It includes information on the presidential election, the impeachment of President Bill Clinton, the Y2K bug, the dot-com bubble, the Columbine High School massacre, the death of Princess Diana, and the rise of the internet. The book also includes a timeline of significant events,

---

## probe_08 — instruction:

> Present statistical evidence demonstrating diphtheria mortality decline in Paris following the introduction and widespread adoption of serotherapy.

### Own reference  (stephen_crane, poetry) — first 600 chars

> The following is a list of the pamphlets already issued by the Society:--  1. Letter from the President announcing the formation of the Society, April 24.  2. Report of the inaugural meeting.  3. Experiments on animals during 1907 in Great Britain and Ireland.  4. Some facts as to the administration of the Act.  5. The value of antitoxin in the treatment of diphtheria.  6. Evidence of Sir Frederick Treves.  7. Yellow fever and malaria.  8. Extinction of Malta fever.  9. Have experiments on animals advanced Therapeutics?  10. The work of the Research Defence Society.  11. Vivisection and medici

### Swap reference  (matthew_arnold, poetry) — first 600 chars

> LECTURE XVII.  RESUME OF DOCTRINE.  Review of the doctrine contained in these lectures, and the three orders of facts on which this doctrine rests, with the relation of each one of them to the modern school that has recognized and developed it, but almost always exaggerated it.--Experience and empiricism.--Reason and idealism.--Sentiment and mysticism.--Theodicea. Defects of different known systems.--The process that conducts to true theodicea, and the character of certainty and reality that this process gives to it.

### **adapter** (conditioned on own ref: stephen_crane)

> {Material Behzeguy-Mathematico-75.~tb.loc.all.Cel._Sede.Fisiol., 17, Ledley's opinion, which is to be found in _Osbon on Small-fry_ (1886), The _S. Francisco_ (1852) had a sensational voyage out, owing to The _S. Francisco_ (1852).--Owing to the assistance given by the The _S. Francisco_ (1852).--Owing to the assistance

### **adapter_swap** (conditioned on swap ref: matthew_arnold)

> To aid in the study of the mortality of the First Empire, civil chief-townsmen were required to furnish the Bureau of Statistics with the information which they could command as to the causes of death in their respective districts during the year.

### **prompted_baseline** (no adapter, just prompt with own-style hint)

> The decline in diphtheria mortality in Paris following the introduction and widespread adoption of serotherapy is a result of the following factors:  1. The introduction of serotherapy in Paris in 1905 was a significant event in the history of diphtheria treatment. Prior to this, diphtheria was a major cause of death in children, with mortality rates as high as 20%. However, with the introduction of serotherapy, mortality rates began to decline rapidly.  2. The widespread adoption of serotherapy in Paris was a result of the efforts of the Pasteur Institute, which played a key role in the

### **no_ref** (base model, no conditioning, no style hint)

> The first diphtheria epidemic in Paris occurred in 1820. The first diphtheria epidemic in Paris occurred in 1820. The first diphtheria epidemic in Paris occurred in 1820. The first diphtheria epidemic in Paris occurred in 1820. The first diphtheria epidemic in Paris occurred in 1820. The first diphtheria epidemic in Paris occurred in 1820. The first diphtheria epidemic in Paris occurred in 1820. The first diphtheria epidemic in Paris occurred in 1820. The first diphtheria epidemic in Paris occurred in

---

