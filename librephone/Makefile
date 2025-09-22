# Copyright (c) 2025 Free Software Foundation, Inc.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

all: typedefs tabledefs

typedefs: typedefs.yaml
	@echo "Generating typedef files for postgresql & python"
	-@./generator.py -t typedefs.yaml

tabledefs: tabledefs.yaml
	@echo "Generating table & class files for python and postgresql"
	-@./generator.py -c tabledefs.yaml

load: typedefs tabledefs
	@echo "Loading generated files into postgres"
	-psql -d devices -f typedefs.sql
	-psql -d devices -f tabledefs.sql

# %.sql: %.yaml
# 	@echo "Generating $@ file for postgresql"
# 	-@./generator.py -t $<

# %.py: %.yaml
# 	@echo "Generating $@ file for python"
# 	-@./generator.py -c $<

# typedefs.py: typedefs.yaml
# typedefs.sql: typedefs.yaml
# tabledefs.py: tabledefs.yaml
# tabledefs.sql: tabledefs.yaml

force:
