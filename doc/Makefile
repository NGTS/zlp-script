SOURCES=$(wildcard *.md)
OUTPUTS=$(SOURCES:.md=.html)

all: $(OUTPUTS)

%.html: %.md
	grip --gfm --export $<

.PHONY: clean

clean:
	@rm -f *.html
