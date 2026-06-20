.PHONY: examples publications

CC = lualatex
EXAMPLES_DIR = examples
RESUME_DIR = examples/resume
CV_DIR = examples/cv
RESUME_SRCS = $(shell find $(RESUME_DIR) -name '*.tex')
CV_SRCS = $(shell find $(CV_DIR) -name '*.tex')

# Mirror the built resume.pdf into the online-CV assets folder (auto-skipped if absent)
ONLINE_PDF_DIR  ?= ../../onlineCV2/assets/pdf
ONLINE_PDF_NAME ?= youhao-hu-cv.pdf

# Auto-generated publication list (from citekeys)
PUB_TEX = $(RESUME_DIR)/publications.tex
PUB_GEN = scripts/gen_publications.py

examples: $(foreach x, coverletter cv resume, $x.pdf)

$(PUB_TEX): $(RESUME_DIR)/publications.bib $(RESUME_DIR)/publications.keys $(PUB_GEN)
	python3 $(PUB_GEN) --bib $(RESUME_DIR)/publications.bib --keys $(RESUME_DIR)/publications.keys --out $@

publications: $(PUB_TEX)

resume.pdf: $(EXAMPLES_DIR)/resume.tex $(RESUME_SRCS) $(PUB_TEX)
	$(CC) -output-directory=$(EXAMPLES_DIR) $<
	@if [ -d "$(ONLINE_PDF_DIR)" ]; then \
		cp "$(EXAMPLES_DIR)/resume.pdf" "$(ONLINE_PDF_DIR)/$(ONLINE_PDF_NAME)"; \
		echo "==> 已镜像到 $(ONLINE_PDF_DIR)/$(ONLINE_PDF_NAME)"; \
	else \
		echo "==> 跳过镜像（目录不存在）：$(ONLINE_PDF_DIR)"; \
	fi

cv.pdf: $(EXAMPLES_DIR)/cv.tex $(CV_SRCS)
	$(CC) -output-directory=$(EXAMPLES_DIR) $<

coverletter.pdf: $(EXAMPLES_DIR)/coverletter.tex
	$(CC) -output-directory=$(EXAMPLES_DIR) $<

clean:
	rm -rf $(EXAMPLES_DIR)/*.pdf
