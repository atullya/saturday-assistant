using System;
using Microsoft.EntityFrameworkCore.Migrations;
using Npgsql.EntityFrameworkCore.PostgreSQL.Metadata;

#nullable disable

namespace TodoApi.Migrations
{
    /// <inheritdoc />
    public partial class InitAll : Migration
    {
        /// <inheritdoc />
        protected override void Up(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.CreateTable(
                name: "Tenants",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    FullName = table.Column<string>(type: "text", nullable: false),
                    Phone = table.Column<string>(type: "text", nullable: false),
                    EmergencyContact = table.Column<string>(type: "text", nullable: false),
                    NationalId = table.Column<string>(type: "text", nullable: false),
                    RoomNumber = table.Column<string>(type: "text", nullable: false),
                    MoveInDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    MonthlyRent = table.Column<decimal>(type: "numeric(10,2)", precision: 10, scale: 2, nullable: false),
                    IsActive = table.Column<bool>(type: "boolean", nullable: false),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Tenants", x => x.Id);
                });

          

            migrationBuilder.CreateTable(
                name: "MonthlyBills",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    TenantId = table.Column<int>(type: "integer", nullable: false),
                    Month = table.Column<int>(type: "integer", nullable: false),
                    Year = table.Column<int>(type: "integer", nullable: false),
                    RentAmount = table.Column<decimal>(type: "numeric(10,2)", precision: 10, scale: 2, nullable: false),
                    ElectricityUnits = table.Column<decimal>(type: "numeric(10,2)", precision: 10, scale: 2, nullable: false),
                    ElectricityRate = table.Column<decimal>(type: "numeric(10,2)", precision: 10, scale: 2, nullable: false),
                    ExtraFees = table.Column<decimal>(type: "numeric(10,2)", precision: 10, scale: 2, nullable: false),
                    ExtraFeeNote = table.Column<string>(type: "text", nullable: true),
                    TotalPaid = table.Column<decimal>(type: "numeric(10,2)", precision: 10, scale: 2, nullable: false, defaultValue: 0m),
                    CreatedAt = table.Column<DateTime>(type: "timestamp with time zone", nullable: false)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_MonthlyBills", x => x.Id);
                    table.ForeignKey(
                        name: "FK_MonthlyBills_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateTable(
                name: "Payments",
                columns: table => new
                {
                    Id = table.Column<int>(type: "integer", nullable: false)
                        .Annotation("Npgsql:ValueGenerationStrategy", NpgsqlValueGenerationStrategy.IdentityByDefaultColumn),
                    TenantId = table.Column<int>(type: "integer", nullable: false),
                    MonthlyBillId = table.Column<int>(type: "integer", nullable: false),
                    AmountPaid = table.Column<decimal>(type: "numeric(10,2)", precision: 10, scale: 2, nullable: false),
                    PaymentDate = table.Column<DateTime>(type: "timestamp with time zone", nullable: false),
                    PaymentMethod = table.Column<string>(type: "text", nullable: false),
                    Note = table.Column<string>(type: "text", nullable: true)
                },
                constraints: table =>
                {
                    table.PrimaryKey("PK_Payments", x => x.Id);
                    table.ForeignKey(
                        name: "FK_Payments_MonthlyBills_MonthlyBillId",
                        column: x => x.MonthlyBillId,
                        principalTable: "MonthlyBills",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                    table.ForeignKey(
                        name: "FK_Payments_Tenants_TenantId",
                        column: x => x.TenantId,
                        principalTable: "Tenants",
                        principalColumn: "Id",
                        onDelete: ReferentialAction.Cascade);
                });

            migrationBuilder.CreateIndex(
                name: "IX_MonthlyBills_TenantId",
                table: "MonthlyBills",
                column: "TenantId");

            migrationBuilder.CreateIndex(
                name: "IX_Payments_MonthlyBillId",
                table: "Payments",
                column: "MonthlyBillId");

            migrationBuilder.CreateIndex(
                name: "IX_Payments_TenantId",
                table: "Payments",
                column: "TenantId");
        }

        /// <inheritdoc />
        protected override void Down(MigrationBuilder migrationBuilder)
        {
            migrationBuilder.DropTable(
                name: "Payments");

    

            migrationBuilder.DropTable(
                name: "MonthlyBills");

            migrationBuilder.DropTable(
                name: "Tenants");
        }
    }
}
