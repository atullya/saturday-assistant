using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using TodoApi.Models;
using TodoApi.Repositories;
using TodoApi.DTOs;
namespace TodoApi.Controllers
{
    [ApiController]
    [Route("api/bills")]
    public class BillsController : ControllerBase
    {
        private readonly IRentRepository _repo;
        public BillsController(IRentRepository repo) => _repo = repo;

        [HttpPost]
        public async Task<IActionResult> CreateBill(CreateBillDto dto)
        {
            var tenant = await _repo.GetTenantByIdAsync(dto.TenantId);
            if (tenant == null) return NotFound("Tenant not found.");

            var bill = new MonthlyBill
            {
                TenantId = dto.TenantId,
                Month = dto.Month,
                Year = dto.Year,
                RentAmount = tenant.MonthlyRent,   // pulled from tenant automatically
                ElectricityUnits = dto.ElectricityUnits,
                ElectricityRate = dto.ElectricityRate,
                ExtraFees = dto.ExtraFees,
                ExtraFeeNote = dto.ExtraFeeNote
            };
            var created = await _repo.CreateBillAsync(bill);
            return Ok(created);


        }

        [HttpGet("{tenantId}/{month}/{year}")]
        public async Task<IActionResult> GetBill(int tenantId, int month, int year)
        {
            var bill = await _repo.GetBillAsync(tenantId, month, year);
            return bill == null ? NotFound() : Ok(bill);
        }

        [HttpGet("dues")]
        public async Task<IActionResult> GetDues() =>
            Ok(await _repo.GetDuesAsync());

        [HttpGet("summary/{month}/{year}")]
        public async Task<IActionResult> GetSummary(int month, int year) =>
            Ok(await _repo.GetMonthlySummaryAsync(month, year));
    }
}