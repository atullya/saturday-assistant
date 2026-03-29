using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using TodoApi.Models;
using TodoApi.DTOs;
using TodoApi.Repositories;

namespace TodoApi.Controllers
{
    [ApiController]
    [Route("api/tenants")]
    public class TenantsController : ControllerBase
    {
        private readonly IRentRepository _repo;
        public TenantsController(IRentRepository repo) => _repo = repo;


        [HttpGet]
        public async Task<IActionResult> GetAll() =>
            Ok(await _repo.GetAllActiveTenantsAsync());

        [HttpGet("archived")]
        public async Task<IActionResult> GetArchived() =>
            Ok(await _repo.GetArchivedTenantsAsync());

        [HttpGet("{id}")]
        public async Task<IActionResult> GetById(int id)
        {
            var tenant = await _repo.GetTenantByIdAsync(id);
            return tenant == null ? NotFound() : Ok(tenant);
        }
        [HttpPost]
        public async Task<IActionResult> Create(CreateTenantDto dto)
        {
            var tenant = new Tenant
            {
                FullName = dto.FullName,
                Phone = dto.Phone,
                EmergencyContact = dto.EmergencyContact,
                NationalId = dto.NationalId,
                RoomNumber = dto.RoomNumber,
                MoveInDate = (DateTime)dto.MoveInDate,
                MonthlyRent = (decimal)dto.MonthlyRent
            };
            var created = await _repo.AddTenantAsync(tenant);
            return CreatedAtAction(nameof(GetById), new { id = created.Id }, created);
        }

        [HttpPut("{id}")]
        public async Task<IActionResult> Update(int id, UpdateTenantDto dto)
        {
            var updated = await _repo.UpdateTenantAsync(id, dto);
            return updated == null ? NotFound() : Ok(updated);
        }

        [HttpDelete("{id}")]
        public async Task<IActionResult> Archive(int id)
        {
            var success = await _repo.ArchiveTenantAsync(id);
            return success ? Ok(new { message = "Tenant archived." }) : NotFound();
        }
    }
}