#!/usr/bin/env python3
"""
Seed script para criar/atualizar os 7 usuários de demonstração do Farol.

Usuários:
- 6 usuários VERTICAL (um por unidade Azul) com vertical_id único cada
- 1 usuário MARKETING com papel MARKETING e vertical_id null

Senha comum: teste123
"""

import sys
import uuid
from typing import Optional

from app.database.database import get_sessionmaker
from app.core.hashing import hash_password
from app.models.enums import PapelUsuario
from app.models.usuario import Usuario
from app.models.vertical import Vertical


DEMO_USERS = [
    {
        "nome": "Azul Linhas Aéreas",
        "email": "linhas.aereas@azul.com.br",
        "papel": PapelUsuario.VERTICAL,
        "vertical_nome": "Azul Linhas Aéreas",
        "senha": "teste123",
    },
    {
        "nome": "Azul Conecta",
        "email": "conecta@azul.com.br",
        "papel": PapelUsuario.VERTICAL,
        "vertical_nome": "Azul Conecta",
        "senha": "teste123",
    },
    {
        "nome": "Azul Cargo Express",
        "email": "cargo@azul.com.br",
        "papel": PapelUsuario.VERTICAL,
        "vertical_nome": "Azul Cargo Express",
        "senha": "teste123",
    },
    {
        "nome": "Azul Viagens",
        "email": "viagens@azul.com.br",
        "papel": PapelUsuario.VERTICAL,
        "vertical_nome": "Azul Viagens",
        "senha": "teste123",
    },
    {
        "nome": "Azul Fidelidade",
        "email": "fidelidade@azul.com.br",
        "papel": PapelUsuario.VERTICAL,
        "vertical_nome": "Azul Fidelidade",
        "senha": "teste123",
    },
    {
        "nome": "Azul TecOps",
        "email": "tecops@azul.com.br",
        "papel": PapelUsuario.VERTICAL,
        "vertical_nome": "Azul TecOps",
        "senha": "teste123",
    },
    {
        "nome": "Marketing",
        "email": "marketing@azul.com.br",
        "papel": PapelUsuario.MARKETING,
        "vertical_nome": None,
        "senha": "teste123",
    },
]


def get_or_create_vertical(db, nome: str) -> uuid.UUID:
    """Obtém ou cria uma vertical pelo nome, retorna o ID."""
    vertical = db.query(Vertical).filter(Vertical.nome == nome).first()
    if vertical:
        return vertical.id
    
    vertical = Vertical(nome=nome, descricao=f"Vertical {nome}", ativa=True)
    db.add(vertical)
    db.flush()
    return vertical.id


def seed_demo_users() -> None:
    """Cria ou atualiza os 7 usuários de demonstração."""
    db = get_sessionmaker()()
    
    try:
        print("=== INICIANDO SEED DE USUÁRIOS DE DEMONSTRAÇÃO ===\n")
        
        # 1. Criar/obter verticais
        print("--- Verticais ---")
        vertical_ids = {}
        for user_data in DEMO_USERS:
            v_nome = user_data["vertical_nome"]
            if v_nome and v_nome not in vertical_ids:
                v_id = get_or_create_vertical(db, v_nome)
                vertical_ids[v_nome] = v_id
                print(f"  Vertical: {v_nome} -> ID: {v_id}")
            elif not v_nome:
                print(f"  Marketing: vertical_id = NULL (opcional)")
        
        # 2. Criar/atualizar usuários
        print("\n--- Usuários ---")
        criados = 0
        atualizados = 0
        
        for user_data in DEMO_USERS:
            email = user_data["email"]
            nome = user_data["nome"]
            papel = user_data["papel"]
            vertical_nome = user_data["vertical_nome"]
            senha = user_data["senha"]
            
            vertical_id = vertical_ids.get(vertical_nome) if vertical_nome else None
            senha_hash = hash_password(senha)
            
            usuario = db.query(Usuario).filter(Usuario.email == email).first()
            
            if usuario:
                # Verificar se precisa atualizar
                precisa_atualizar = False
                if usuario.senha_hash != senha_hash:
                    usuario.senha_hash = senha_hash
                    precisa_atualizar = True
                if usuario.papel != papel:
                    usuario.papel = papel
                    precisa_atualizar = True
                if usuario.vertical_id != vertical_id:
                    usuario.vertical_id = vertical_id
                    precisa_atualizar = True
                if not usuario.ativo:
                    usuario.ativo = True
                    precisa_atualizar = True
                
                if precisa_atualizar:
                    atualizados += 1
                    print(f"  ATUALIZADO: {nome} ({email}) | Papel: {papel.value} | Vertical: {vertical_id or 'NULL'}")
                else:
                    print(f"  OK: {nome} ({email}) | Papel: {papel.value} | Vertical: {vertical_id or 'NULL'}")
            else:
                usuario = Usuario(
                    nome=nome,
                    email=email,
                    senha_hash=senha_hash,
                    papel=papel,
                    vertical_id=vertical_id,
                    ativo=True,
                )
                db.add(usuario)
                criados += 1
                print(f"  CRIADO: {nome} ({email}) | Papel: {papel.value} | Vertical: {vertical_id or 'NULL'}")
        
        db.commit()
        
        # 3. Resumo final
        print("\n=== RESUMO FINAL ===")
        print(f"  Usuários criados: {criados}")
        print(f"  Usuários atualizados: {atualizados}")
        print(f"  Total de usuários de demo: {len(DEMO_USERS)}")
        
        print("\n=== VERIFICAÇÃO FINAL ===")
        for user_data in DEMO_USERS:
            email = user_data["email"]
            usuario = db.query(Usuario).filter(Usuario.email == email).first()
            if usuario:
                v_nome = usuario.vertical.nome if usuario.vertical else "NULL"
                print(f"  ✓ {usuario.nome} | {usuario.email} | {usuario.papel.value} | Vertical: {v_nome} | Ativo: {usuario.ativo}")
            else:
                print(f"  ✗ {user_data['nome']} ({email}) - NÃO ENCONTRADO!")
        
        print("\n=== SEED CONCLUÍDO COM SUCESSO ===")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ERRO: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_demo_users()