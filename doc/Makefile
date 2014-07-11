SOURCES=$(wildcard *.twiki)
MARKDOWN=$(SOURCES:.twiki=.md)
OUTPUTS=$(MARKDOWN:.md=.html)
PDFOUTPUTS=$(MARKDOWN:.md=.pdf)

all: $(OUTPUTS)
pdf: $(PDFOUTPUTS)

%.pdf: %.md
	pandoc -s $< -o $@

%.md: %.twiki
	perl twiki2md.pl $< > $@

%.html: %.md
	pandoc $< -o $@

.PHONY: clean

clean:
	@rm -f *.html *.pdf
