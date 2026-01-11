# Minimal makefile for Sphinx documentation
#

# You can set these variables from the command line, and also
# from the environment for the first two.
SPHINXOPTS    ?=
SPHINXBUILD   ?= sphinx-build
SOURCEDIR     = .
BUILDDIR      = _build

# Put it first so that "make" without argument is like "make help".
help:
	@$(SPHINXBUILD) -M help "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

.PHONY: help Makefile html clean

CSV_FILES := objectgroup_acc_conv.csv objectgroup_adc.csv objectgroup_bat_mng_struct.csv objectgroup_battery.csv objectgroup_battery_placeholder.csv objectgroup_buf_v_control.csv objectgroup_can_bus.csv objectgroup_cs_map.csv objectgroup_cs_neg.csv objectgroup_db.csv objectgroup_dc_conv.csv objectgroup_display_struct.csv objectgroup_energy.csv objectgroup_fault.csv objectgroup_flash_param.csv objectgroup_flash_rtc.csv objectgroup_grid_lt.csv objectgroup_grid_mon.csv objectgroup_g_sync.csv objectgroup_hw_test.csv objectgroup_io_board.csv objectgroup_iso_struct.csv objectgroup_line_mon.csv objectgroup_logger.csv objectgroup_modbus.csv objectgroup_net.csv objectgroup_nsm.csv objectgroup_others.csv objectgroup_partition.csv objectgroup_power_mng.csv objectgroup_p_rec.csv objectgroup_prim_sm.csv objectgroup_rb485.csv objectgroup_switch_on_cond.csv objectgroup_temperature.csv objectgroup_wifi.csv

html: $(CSV_FILES)
	@$(SPHINXBUILD) -M html "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)

clean:
	@$(SPHINXBUILD) -M clean "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
	rm -f objectgroup_*.csv

%.csv: ../src/rctclient/registry.py
	./generate_registry.py

../src/rctclient/registry.py:
	@:

# Catch-all target: route all unknown targets to Sphinx using the new
# "make mode" option.  $(O) is meant as a shortcut for $(SPHINXOPTS).
%: Makefile
	@$(SPHINXBUILD) -M $@ "$(SOURCEDIR)" "$(BUILDDIR)" $(SPHINXOPTS) $(O)
