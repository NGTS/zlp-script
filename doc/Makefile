SOURCES=$(wildcard *.md)
OUTPUTS=$(SOURCES:.md=.html)

all: $(OUTPUTS)

%.pdf: %.md
	pandoc -s $< -o $@

%.html: %.md
	grip --gfm --export $<

.PHONY: clean

clean:
	@rm -f *.html
