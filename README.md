# BBHelper (needs fix!)

## Background Infos
BlindBooking Helper has been my first major project with Python. The project combines **web scraping**, **parsing (with lxml)** and **Image/Pattern recognition (with OpenCV)**. Due to the fact that the structure of the scraped webpages have been constantly modified over the last years, the script is currently not running but with a little modification it should work again!
Furthermore, since this has been my first project, the source code is a bit messy and could be optimized.

*Disclaimer: This script is not for commercial use! According to Germanwings' terms of use, it is not allowed to reproduce or collect data for any commercial purposes!*

Tasks to optimize/fix are:
* Finding a faster substitute for the extensive mechanize module, which handles cookies and allows to fill and send website forms but is also quite slow! 
* Optimizing the parsing process! In the very beginning, I parsed websites by saving the source code as a string and searched for certain HTML tags etc., which takes a very long time compared to using lxml with XPath - the way I am doing it nowadays. The source code of BlindBooking Helper for parsing content has been only partially replaced with lxml/XPath nodes so far.
* Analyze website source code for new identifiers and new/changed labellings of tags or different structures to fix the broken parts of the script!

## What's it all about?
BlindBooking Helper is a tool that enables you to book a return flight to a desired destination for approx. 66 EUR - even if you want to fly tomorrow!

#### What is the Germanwings BlindBooking program?
Germanwings offers a great BlindBooking/surprise flight program, that enables you to book low-priced flights (66 EUR for a return flight). Unfortunately you don't know exactly where you're actually flying to until you've booked the flight. There are several programs (e.g. Party, Culture, Shopping) that contain destinations Germanwings is operating. For an extra fee you may rule out undesired destinations. 

So, to sum it up, here is the trade-off: you pay very less but you only get to know the destination of your flight after booking it!

With BlindBooking Helper you are able to know the destination of the flight beforehand! 



#### Workflow
BlindBooking Helper comes into play right after you've selected your blindbooking flight program on the Germanwings website and provided information about undesired destinations, travel dates and number of passangers. The second step of the booking procedure first loads the departures and their corresponding programs and destinations from the Germanwings Website.
