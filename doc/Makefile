SOURCES=$(wildcard *.md)
OUTPUTS=$(SOURCES:.md=.html)
PDFOUTPUTS=$(SOURCES:.md=.pdf)

all: $(OUTPUTS)
pdf: $(PDFOUTPUTS)

%.pdf: %.md
	pandoc -s $< -o $@

%.html: %.md
	pandoc -s $< -o $@

.PHONY: clean

clean:
	@rm -f *.html *.pdf
