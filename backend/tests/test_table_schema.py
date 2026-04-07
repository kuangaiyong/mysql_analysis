"""
Table schema tests - 100% coverage target
"""

import pytest
from decimal import Decimal


class TestTableSchema:
    """Table schema tests for 100% coverage"""

    def test_table_info_create_all_fields(self):
        """Test table info create with all fields"""
        from app.schemas.table import TableInfoCreate

        table = TableInfoCreate(
            table_name="products",
            database_name="mydb",
            table_type="base",
            engine="InnoDB",
            row_count=10000,
            data_length=1024000,
            index_length=512000,
        )

        assert table.table_name == "products"
        assert table.database_name == "mydb"
        assert table.table_type == "base"
        assert table.row_count == 10000

    def test_table_info_minimal(self):
        """Test table info create minimal"""
        from app.schemas.table import TableInfoCreate

        table = TableInfoCreate(table_name="users")

        assert table.table_name == "users"
        assert table.database_name is None

    def test_table_info_all_types(self):
        """Test table info all types"""
        from app.schemas.table import TableType, TableInfoCreate

        types = [TableType.BASE, TableType.VIEW, TableType.TEMPORARY]

        for table_type in types:
            table = TableInfoCreate(table_name="test_table", table_type=table_type)

            assert table.table_type == table_type

    def test_table_info_all_engines(self):
        """Test table info all engines"""
        from app.schemas.table import TableInfoCreate

        engines = ["InnoDB", "MyISAM", "MEMORY", "CSV"]

        for engine in engines:
            table = TableInfoCreate(table_name="test_table", engine=engine)

            assert table.engine == engine

    def test_table_info_row_count_zero(self):
        """Test table info with zero row count"""
        from app.schemas.table import TableInfoCreate

        table = TableInfoCreate(table_name="empty_table", row_count=0)

        assert table.row_count == 0

    def test_table_info_negative_row_count(self):
        """Test table info with negative row count validation"""
        from app.schemas.table import TableInfoCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TableInfoCreate(
                table_name="test",
                row_count=-1,  # Negative should fail validation
            )

    def test_table_info_large_values(self):
        """Test table info with large values"""
        from app.schemas.table import TableInfoCreate
        from decimal import Decimal

        table = TableInfoCreate(
            table_name="large_table",
            row_count=999999999999,
            data_length=Decimal("999999999999"),
            index_length=Decimal("999999999999"),
        )

        assert table.row_count == 999999999999

    def test_table_info_without_database(self):
        """Test table info without database name"""
        from app.schemas.table import TableInfoCreate

        table = TableInfoCreate(table_name="test_table")

        assert table.database_name is None

    def test_column_info_create_all_types(self):
        """Test column info create all data types"""
        from app.schemas.table import ColumnInfoCreate

        types = ["INT", "VARCHAR", "TEXT", "DATETIME", "DECIMAL", "BLOB", "JSON"]

        for col_type in types:
            col = ColumnInfoCreate(
                column_name="test_col",
                data_type=col_type,
                is_nullable=True,
                column_key="",
            )

            assert col.data_type == col_type

    def test_column_info_with_max_length(self):
        """Test column info with max length"""
        from app.schemas.table import ColumnInfoCreate

        col = ColumnInfoCreate(
            column_name="email",
            data_type="VARCHAR",
            max_length=255,
            is_nullable=False,
            column_key="UNI",
        )

        assert col.max_length == 255
        assert col.column_key == "UNI"

    def test_column_info_all_keys(self):
        """Test column info all key types"""
        from app.schemas.table import ColumnInfoCreate

        keys = ["PRIMARY", "UNI", "MUL", ""]

        for key in keys:
            col = ColumnInfoCreate(
                column_name="test_col", data_type="INT", column_key=key
            )

            assert col.column_key == key

    def test_column_info_with_default_value(self):
        """Test column info with default value"""
        from app.schemas.table import ColumnInfoCreate

        col = ColumnInfoCreate(
            column_name="status",
            data_type="VARCHAR",
            default_value="active",
            is_nullable=True,
        )

        assert col.default_value == "active"

    def test_column_info_without_nullable(self):
        """Test column info without nullable"""
        from app.schemas.table import ColumnInfoCreate

        col = ColumnInfoCreate(column_name="test_col", data_type="INT")

        assert col.is_nullable is None

    def test_column_info_numeric_types(self):
        """Test column info numeric types"""
        from app.schemas.table import ColumnInfoCreate
        from decimal import Decimal

        numeric_types = [
            "TINYINT",
            "SMALLINT",
            "INT",
            "BIGINT",
            "FLOAT",
            "DOUBLE",
            "DECIMAL(10,2)",
        ]

        for col_type in numeric_types:
            col = ColumnInfoCreate(column_name=f"test_{col_type}", data_type=col_type)

            assert col.data_type == col_type

    def test_column_info_auto_increment(self):
        """Test column info with auto increment"""
        from app.schemas.table import ColumnInfoCreate

        col = ColumnInfoCreate(
            column_name="id", data_type="INT", is_auto_increment=True, column_key="PRI"
        )

        assert col.is_auto_increment is True

    def test_foreign_key_create(self):
        """Test foreign key create"""
        from app.schemas.table import ForeignKeyCreate

        fk = ForeignKeyCreate(
            column_name="user_id",
            referenced_table="users",
            referenced_column="id",
            on_delete="CASCADE",
        )

        assert fk.referenced_table == "users"
        assert fk.on_delete == "CASCADE"

    def test_foreign_key_all_on_delete(self):
        """Test foreign key all on delete actions"""
        from app.schemas.table import ForeignKeyCreate

        actions = ["CASCADE", "SET NULL", "RESTRICT", "NO ACTION"]

        for action in actions:
            fk = ForeignKeyCreate(
                column_name="test_col",
                referenced_table="ref_table",
                referenced_column="id",
                on_delete=action,
            )

            assert fk.on_delete == action

    def test_foreign_key_on_update(self):
        """Test foreign key with on update"""
        from app.schemas.table import ForeignKeyCreate

        fk = ForeignKeyCreate(
            column_name="test_col",
            referenced_table="ref_table",
            referenced_column="id",
            on_delete="CASCADE",
            on_update="CASCADE",
        )

        assert fk.on_update == "CASCADE"

    def test_foreign_key_without_on_delete(self):
        """Test foreign key without on delete"""
        from app.schemas.table import ForeignKeyCreate

        fk = ForeignKeyCreate(
            column_name="test_col", referenced_table="ref_table", referenced_column="id"
        )

        assert fk.on_delete is None

    def test_foreign_key_with_constraint_name(self):
        """Test foreign key with constraint name"""
        from app.schemas.table import ForeignKeyCreate

        fk = ForeignKeyCreate(
            column_name="test_col",
            referenced_table="ref_table",
            referenced_column="id",
            constraint_name="fk_test_table_users",
        )

        assert fk.constraint_name == "fk_test_table_users"

    def test_table_statistics_create(self):
        """Test table statistics create"""
        from app.schemas.table import TableStatisticsCreate
        from decimal import Decimal

        stats = TableStatisticsCreate(
            total_rows=10000,
            data_length=Decimal("1024000"),
            index_length=Decimal("512000"),
            avg_row_length=Decimal("102.4"),
            max_row_length=Decimal("10240"),
        )

        assert stats.total_rows == 10000
        assert stats.avg_row_length == Decimal("102.4")

    def test_table_statistics_zero_rows(self):
        """Test table statistics with zero rows"""
        from app.schemas.table import TableStatisticsCreate

        stats = TableStatisticsCreate(
            total_rows=0,
            data_length=0,
            index_length=0,
            avg_row_length=Decimal("0"),
            max_row_length=Decimal("0"),
        )

        assert stats.total_rows == 0

    def test_table_statistics_negative_values(self):
        """Test table statistics with negative values"""
        from app.schemas.table import TableStatisticsCreate
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            TableStatisticsCreate(
                total_rows=-1  # Negative should fail
            )

    def test_table_comparison_create(self):
        """Test table comparison create"""
        from app.schemas.table import TableComparisonCreate

        comparison = TableComparisonCreate(
            table1_name="products",
            table2_name="orders",
            metric="row_count",
            difference=1000,
            percentage=Decimal("10.0"),
        )

        assert comparison.table1_name == "products"
        assert comparison.difference == 1000
        assert comparison.percentage == Decimal("10.0")

    def test_table_comparison_all_metrics(self):
        """Test table comparison all metrics"""
        from app.schemas.table import TableComparisonCreate
        from decimal import Decimal

        metrics = ["row_count", "data_length", "index_length", "avg_row_length"]

        for metric in metrics:
            comparison = TableComparisonCreate(
                table1_name="table1",
                table2_name="table2",
                metric=metric,
                difference=100,
            )

            assert comparison.metric == metric

    def test_table_info_update(self):
        """Test table info update"""
        from app.schemas.table import TableInfoUpdate

        update = TableInfoUpdate(table_type="view", engine="MyISAM", row_count=5000)

        assert update.table_type == "view"
        assert update.row_count == 5000

    def test_column_info_update(self):
        """Test column info update"""
        from app.schemas.table import ColumnInfoUpdate

        update = ColumnInfoUpdate(is_nullable=False, default_value="updated_value")

        assert update.is_nullable is False
        assert update.default_value == "updated_value"

    def test_table_list_response(self):
        """Test table list response"""
        from app.schemas.table import TableListResponse, TableInfoResponse
        from decimal import Decimal

        tables = [
            TableInfoResponse(
                table_name="users",
                database_name="mydb",
                row_count=1000,
                data_length=Decimal("10000"),
            ),
            TableInfoResponse(
                table_name="orders",
                database_name="mydb",
                row_count=5000,
                data_length=Decimal("50000"),
            ),
        ]

        response = TableListResponse(total=2, items=tables)

        assert response.total == 2
        assert len(response.items) == 2

    def test_table_structure_response(self):
        """Test table structure response"""
        from app.schemas.table import TableStructureResponse, ColumnInfoResponse
        from decimal import Decimal

        columns = [
            ColumnInfoResponse(
                column_name="id", data_type="INT", is_nullable=False, column_key="PRI"
            ),
            ColumnInfoResponse(
                column_name="email",
                data_type="VARCHAR",
                is_nullable=False,
                max_length=255,
            ),
        ]

        response = TableStructureResponse(
            table_name="users", database_name="mydb", row_count=1000, columns=columns
        )

        assert response.table_name == "users"
        assert len(response.columns) == 2

    def test_foreign_keys_response(self):
        """Test foreign keys response"""
        from app.schemas.table import ForeignKeysResponse, ForeignKeyResponse

        foreign_keys = [
            ForeignKeyResponse(
                column_name="user_id",
                referenced_table="users",
                referenced_column="id",
                on_delete="CASCADE",
            ),
            ForeignKeyResponse(
                column_name="order_id",
                referenced_table="orders",
                referenced_column="id",
                on_delete="SET NULL",
            ),
        ]

        response = ForeignKeysResponse(table_name="orders", foreign_keys=foreign_keys)

        assert response.table_name == "orders"
        assert len(response.foreign_keys) == 2

    def test_table_analyzer_response(self):
        """Test table analyzer response"""
        from app.schemas.table import TableAnalyzerResponse, TableAnalysisResult

        results = [
            TableAnalysisResult(
                table_name="users",
                analysis_type="missing_index",
                recommendation="Add index on email column",
                severity="warning",
            ),
            TableAnalysisResult(
                table_name="orders",
                analysis_type="large_table",
                recommendation="Consider partitioning",
                severity="info",
            ),
        ]

        response = TableAnalyzerResponse(total=2, results=results)

        assert response.total == 2
        assert len(response.results) == 2
