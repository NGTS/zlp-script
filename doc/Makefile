SOURCES=$(wildcard *.md)
OUTPUTS=$(SOURCES:.md=.html)

all: $(OUTPUTS)

%.html: %.md
	pandoc $< -o $@

.PHONY: clean

clean:
	@rm -f *.html
