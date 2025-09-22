# app.py - VERSÃO COMPLETA E ADAPTADA PARA O RENDER

import os # 👈 ADICIONADO para ler variáveis de ambiente
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text, Float, String, Integer
from werkzeug.security import generate_password_hash, check_password_hash
import pandas as pd
import io

app = Flask(__name__)
CORS(app)

# 🔧 Configuração do banco PostgreSQL - MODIFICADO PARA O RENDER
# A URL do banco de dados será lida da variável de ambiente 'DATABASE_URL' fornecida pelo Render
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# 🧩 Novo modelo de Usuário para gerenciamento de acesso
class Usuario(db.Model):
    __tablename__ = 'usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    senha = db.Column(db.String(255), nullable=False)
    acesso = db.Column(db.String(20), nullable=False, default='Usuario') # 'Administrador' ou 'Usuario'

# 🧩 Outros modelos existentes
class Proprietario(db.Model):
    __tablename__ = 'proprietarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpfcnpj = db.Column(db.String(20), nullable=False)
    telefone = db.Column(db.String(20), nullable=False)

class CadastroReurb(db.Model):
    __tablename__ = 'cadastros_reurb'
    id = db.Column(db.Integer, primary_key=True)
    req_nome = db.Column(db.String(150))
    req_cpf = db.Column(db.String(20))
    req_rg = db.Column(db.String(20))
    req_data_nasc = db.Column(db.String(20))
    req_nacionalidade = db.Column(db.String(50))
    req_estado_civil = db.Column(db.String(30))
    conj_nome = db.Column(db.String(150))
    conj_cpf = db.Column(db.String(20))
    req_profissao = db.Column(db.String(100))
    req_telefone = db.Column(db.String(30))
    req_email = db.Column(db.String(150))
    req_cep_atual = db.Column(db.String(15))
    req_logradouro_atual = db.Column(db.String(150))
    req_numero_atual = db.Column(db.String(20))
    req_complemento_atual = db.Column(db.String(100))
    req_bairro_atual = db.Column(db.String(100))
    req_cidade_atual = db.Column(db.String(100))
    req_uf_atual = db.Column(db.String(2))
    imovel_cep = db.Column(db.String(15))
    imovel_logradouro = db.Column(db.String(150))
    imovel_numero = db.Column(db.String(20))
    imovel_complemento = db.Column(db.String(100))
    imovel_bairro = db.Column(db.String(100))
    imovel_cidade = db.Column(db.String(100))
    imovel_uf = db.Column(db.String(2))
    inscricao_imobiliaria = db.Column(db.String(30))
    imovel_area_total = db.Column(db.Float)
    imovel_area_construida = db.Column(db.Float)
    imovel_uso = db.Column(db.String(30))
    imovel_tipo_construcao = db.Column(db.String(30))
    imovel_data_ocupacao = db.Column(db.String(20))
    imovel_forma_ocupacao = db.Column(db.Text)
    imovel_docs_posse = db.Column(db.Text)
    imovel_fotos = db.Column(db.Text)
    imovel_croqui = db.Column(db.Text)
    confrontante_ld = db.Column(db.String(200))
    confrontante_le = db.Column(db.String(200))
    confrontante_fundo = db.Column(db.String(200))
    confrontante_frente = db.Column(db.String(200))
    reurb_finalidade_moradia = db.Column(db.String(50))
    reurb_renda_familiar = db.Column(db.Float)
    reurb_propriedade = db.Column(db.String(30))
    reurb_infra_necessaria = db.Column(db.String(30))
    reurb_riscos = db.Column(db.String(30))
    reurb_riscos_descricao = db.Column(db.Text)
    reurb_outro_imovel = db.Column(db.String(10))
    reurb_cadunico = db.Column(db.String(10))

class Construcao(db.Model):
    __tablename__ = 'construcoes'
    id = db.Column(db.Integer, primary_key=True)
    cadastro_id = db.Column(db.Integer, db.ForeignKey('cadastros_reurb.id'))
    area_total = db.Column(db.Float)
    area_construida = db.Column(db.Float)
    uso = db.Column(db.String(50))
    padrao = db.Column(db.String(50))
    tipo = db.Column(db.String(50))
    cadastro = db.relationship("CadastroReurb", backref=db.backref("construcoes", lazy=True, cascade="all, delete-orphan"))

class PGV(db.Model):
    __tablename__ = 'pgv'
    id = db.Column(Integer, primary_key=True)
    descricao = db.Column(String(150), nullable=False)
    valor_m2 = db.Column(Float, nullable=False)

class PadraoConstrutivo(db.Model):
    __tablename__ = 'padroes_construtivos'
    id = db.Column(Integer, primary_key=True)
    descricao = db.Column(String(150), nullable=False)
    valor_m2 = db.Column(Float, nullable=False)

class ValorLogradouro(db.Model):
    __tablename__ = 'valores_logradouro'
    id = db.Column(Integer, primary_key=True)
    logradouro = db.Column(String(150), nullable=False)
    valor_m2 = db.Column(Float, nullable=False)

class AliquotaIPTU(db.Model):
    __tablename__ = 'aliquotas_iptu'
    id = db.Column(Integer, primary_key=True)
    tipo = db.Column(db.String(150), nullable=False)
    aliquota = db.Column(db.Float, nullable=False)

# 📦 Criação das tabelas
with app.app_context():
    db.create_all()

# ✅ ROTA DE LOGIN MODIFICADA
@app.route('/api/login', methods=['POST'])
def login():
    dados = request.get_json()
    usuario_str = dados.get('usuario')
    senha = dados.get('senha')

    usuario = Usuario.query.filter_by(usuario=usuario_str).first()
    if usuario and check_password_hash(usuario.senha, senha):
        return jsonify({"sucesso": True, "acesso": usuario.acesso, "mensagem": "Login bem-sucedido!"})
    else:
        return jsonify({"sucesso": False, "mensagem": "Usuário ou senha incorretos."})

# 🚀 ROTAS PARA GERENCIAMENTO DE USUÁRIOS
@app.route('/api/usuarios', methods=['POST'])
def criar_usuario():
    dados = request.get_json()
    senha_hash = generate_password_hash(dados['senha'])
    novo_usuario = Usuario(
        nome=dados['nome'],
        usuario=dados['usuario'],
        senha=senha_hash,
        acesso=dados['acesso']
    )
    db.session.add(novo_usuario)
    db.session.commit()
    return jsonify({"sucesso": True, "mensagem": "Usuário criado com sucesso!"}), 201

@app.route('/api/usuarios', methods=['GET'])
def listar_usuarios():
    usuarios = Usuario.query.all()
    lista = [{
        "id": u.id,
        "nome": u.nome,
        "usuario": u.usuario,
        "acesso": u.acesso
    } for u in usuarios]
    return jsonify(lista), 200

@app.route('/api/usuarios/<int:id>', methods=['PUT'])
def atualizar_usuario(id):
    dados = request.get_json()
    usuario = Usuario.query.get_or_404(id)
    usuario.nome = dados['nome']
    usuario.usuario = dados['usuario']
    if 'senha' in dados and dados['senha']:
        usuario.senha = generate_password_hash(dados['senha'])
    usuario.acesso = dados['acesso']
    db.session.commit()
    return jsonify({"sucesso": True, "mensagem": "Usuário atualizado com sucesso!"}), 200

@app.route('/api/usuarios/<int:id>', methods=['DELETE'])
def excluir_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    db.session.delete(usuario)
    db.session.commit()
    return jsonify({"sucesso": True, "mensagem": "Usuário excluído com sucesso!"}), 200

@app.route('/api/usuarios/<int:id>', methods=['GET'])
def obter_usuario(id):
    usuario = Usuario.query.get_or_404(id)
    return jsonify({
        "id": usuario.id,
        "nome": usuario.nome,
        "usuario": usuario.usuario,
        "acesso": usuario.acesso
    }), 200

# Outras rotas permanecem inalteradas
# ... (manter todas as rotas de Cadastro, Planta Genérica, etc.) ...
@app.route('/api/health', methods=['GET'])
def health_check():
    try:
        db.session.execute(text('SELECT 1'))
        return jsonify({'status': 'ok', 'mensagem': 'Conectado ao banco de dados'}), 200
    except Exception as e:
        return jsonify({'status': 'erro', 'mensagem': str(e)}), 500

@app.route('/api/novo_cadastro_reurb', methods=['POST'])
def novo_cadastro_reurb():
    dados = request.get_json()
    modelo_columns = [c.name for c in CadastroReurb.__table__.columns]
    dados_filtrados = {key: value for key, value in dados.items() if key in modelo_columns}

    for campo in ['imovel_area_total', 'imovel_area_construida', 'reurb_renda_familiar']:
        if dados_filtrados.get(campo) == "" or dados_filtrados.get(campo) is None:
            dados_filtrados[campo] = None
        else:
            try:
                dados_filtrados[campo] = float(dados_filtrados[campo])
            except (ValueError, TypeError):
                dados_filtrados[campo] = None
    try:
        novo = CadastroReurb(**dados_filtrados)
        db.session.add(novo)
        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": "Cadastro REURB salvo com sucesso!"}), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route('/api/novo_cadastro_reurb/listar', methods=['GET'])
def listar_cadastros_reurb():
    todos = CadastroReurb.query.all()
    lista = []

    for cad in todos:
        vvt, vvc, vvi, iptu = 0.0, 0.0, 0.0, 0.0
        try:
            if cad.imovel_logradouro and cad.imovel_area_total:
                valor_m2_terreno = ValorLogradouro.query.filter_by(logradouro=cad.imovel_logradouro).first()
                if valor_m2_terreno: vvt = cad.imovel_area_total * valor_m2_terreno.valor_m2
            if cad.imovel_tipo_construcao and cad.imovel_area_construida:
                padrao_construtivo = PadraoConstrutivo.query.filter_by(descricao=cad.imovel_tipo_construcao).first()
                if padrao_construtivo: vvc = cad.imovel_area_construida * padrao_construtivo.valor_m2
            vvi = vvt + vvc
            if cad.imovel_uso and vvi > 0:
                aliquota_iptu = AliquotaIPTU.query.filter(AliquotaIPTU.tipo.ilike(f"%{cad.imovel_uso}%")).first()
                if aliquota_iptu: iptu = vvi * (aliquota_iptu.aliquota / 100.0)
        except Exception as e:
            print(f"Erro ao calcular VVI/IPTU para o cadastro ID {cad.id}: {e}")

        lista.append({
            "id": cad.id, "nome": cad.req_nome, "cpf": cad.req_cpf, "rg": cad.req_rg,
            "telefone": cad.req_telefone, "email": cad.req_email,
            "endereco": f"{cad.imovel_logradouro or ''}, {cad.imovel_numero or ''}",
            "inscricao_imobiliaria": cad.inscricao_imobiliaria,
            "area_total": cad.imovel_area_total, "area_construida": cad.imovel_area_construida,
            "renda_familiar": cad.reurb_renda_familiar,
            "vvt": vvt,
            "vvc": vvc,
            "vvi": vvi,
            "iptu": iptu,
            "tipo_reurb": "REURB-S" if cad.reurb_renda_familiar and cad.reurb_renda_familiar <= 4000 else "REURB-E"
        })
    return jsonify(lista), 200

@app.route('/api/novo_cadastro_reurb/<int:id>', methods=['GET'])
def obter_cadastro_reurb(id):
    try:
        cadastro = CadastroReurb.query.get(id)
        if not cadastro:
            return jsonify({"sucesso": False, "erro": "Cadastro não encontrado"}), 404
        dados_cadastro = {c.name: getattr(cadastro, c.name) for c in cadastro.__table__.columns}
        return jsonify(dados_cadastro), 200
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route('/api/novo_cadastro_reurb/<int:id>', methods=['PUT'])
def atualizar_cadastro_reurb(id):
    try:
        cadastro = CadastroReurb.query.get(id)
        if not cadastro:
            return jsonify({"sucesso": False, "erro": "Cadastro não encontrado"}), 404
        dados = request.get_json()
        for key, value in dados.items():
            if key in ['imovel_area_total', 'imovel_area_construida', 'reurb_renda_familiar']:
                if value == "" or value is None:
                    value = None
                else:
                    try:
                        value = float(value)
                    except (ValueError, TypeError):
                        value = None
            if hasattr(cadastro, key):
                setattr(cadastro, key, value)
        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": "Cadastro atualizado com sucesso!"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route('/api/novo_cadastro_reurb/<int:id>', methods=['DELETE'])
def excluir_cadastro_reurb(id):
    cadastro = CadastroReurb.query.get(id)
    if not cadastro:
        return jsonify({"sucesso": False, "erro": "Cadastro não encontrado"}), 404
    try:
        Construcao.query.filter_by(cadastro_id=id).delete()
        db.session.delete(cadastro)
        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": "Cadastro excluído com sucesso"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route('/api/construcoes/<int:cadastro_id>', methods=['POST'])
def adicionar_construcao(cadastro_id):
    dados = request.get_json()
    nova = Construcao(
        cadastro_id=cadastro_id, area_total=dados.get("area_total"),
        area_construida=dados.get("area_construida"), uso=dados.get("uso"),
        padrao=dados.get("padrao"), tipo=dados.get("tipo")
    )
    db.session.add(nova)
    db.session.commit()
    return jsonify({"sucesso": True, "mensagem": "Construção salva com sucesso!"}), 201

@app.route('/api/construcoes/<int:cadastro_id>', methods=['GET'])
def listar_construcoes(cadastro_id):
    construcoes = Construcao.query.filter_by(cadastro_id=cadastro_id).all()
    return jsonify([{
        "id": c.id, "area_total": c.area_total, "area_construida": c.area_construida,
        "uso": c.uso, "padrao": c.padrao, "tipo": c.tipo
    } for c in construcoes]), 200

@app.route('/api/construcoes/<int:id>', methods=['DELETE'])
def excluir_construcao(id):
    construcao = Construcao.query.get(id)
    if not construcao:
        return jsonify({"sucesso": False, "erro": "Construção não encontrada"}), 404
    try:
        db.session.delete(construcao)
        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": "Construção excluída com sucesso"}), 200
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route('/api/planta_generica/<string:tipo>', methods=['GET', 'POST'])
def planta_generica_crud(tipo):
    model_map = {
        'pgv': (PGV, lambda item: {"id": item.id, "descricao": item.descricao, "valor_m2": item.valor_m2}),
        'padroes': (PadraoConstrutivo, lambda item: {"id": item.id, "descricao": item.descricao, "valor_m2": item.valor_m2}),
        'logradouros': (ValorLogradouro, lambda item: {"id": item.id, "logradouro": item.logradouro, "valor_m2": item.valor_m2}),
        'aliquotas': (AliquotaIPTU, lambda item: {"id": item.id, "tipo": item.tipo, "aliquota": item.aliquota})
    }
    if tipo not in model_map:
        return jsonify({"sucesso": False, "erro": "Tipo de planta genérica inválido"}), 400
    
    model, serialize = model_map[tipo]
    try:
        if request.method == 'POST':
            dados = request.get_json()
            novo_item = model(**dados)
            db.session.add(novo_item)
            db.session.commit()
            return jsonify({"sucesso": True, "mensagem": f"{tipo.upper()} salvo com sucesso!"}), 201
        elif request.method == 'GET':
            todos_itens = model.query.all()
            return jsonify([serialize(item) for item in todos_itens]), 200
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500

@app.route('/api/planta_generica/<string:tipo>/<int:item_id>', methods=['DELETE'])
def excluir_planta_generica_item(tipo, item_id):
    model_map = {'pgv': PGV, 'padroes': PadraoConstrutivo, 'logradouros': ValorLogradouro, 'aliquotas': AliquotaIPTU}
    if tipo not in model_map:
        return jsonify({"sucesso": False, "erro": "Tipo de planta genérica inválido"}), 400
    
    model = model_map[tipo]
    try:
        item = model.query.get(item_id)
        if not item:
            return jsonify({"sucesso": False, "erro": "Item não encontrado."}), 404
        db.session.delete(item)
        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": f"{tipo.upper()} excluído com sucesso!"}), 200
    except Exception as e:
        return jsonify({"sucesso": False, "erro": str(e)}), 500
        
# =======================================================================
# INÍCIO: NOVAS ROTAS PARA IMPORTAÇÃO E EXPORTAÇÃO DE DADOS
# =======================================================================

@app.route('/api/importar', methods=['POST'])
def importar_dados():
    if 'arquivo' not in request.files:
        return jsonify({"sucesso": False, "erro": "Nenhum arquivo enviado."}), 400
    
    arquivo = request.files['arquivo']
    if arquivo.filename == '':
        return jsonify({"sucesso": False, "erro": "Nenhum arquivo selecionado."}), 400

    try:
        # Leitura de Excel ou CSV
        if arquivo.filename.endswith('.xlsx'):
            df = pd.read_excel(arquivo)
        elif arquivo.filename.endswith('.csv'):
            try:
                df = pd.read_csv(arquivo, sep=None, engine='python', encoding='utf-8-sig')
            except Exception:
                try:
                    df = pd.read_csv(arquivo, sep=';', encoding='utf-8-sig')
                except Exception:
                    df = pd.read_csv(arquivo, sep=',', encoding='utf-8-sig')
        else:
            return jsonify({"sucesso": False, "erro": "Formato de arquivo não suportado. Use .xlsx ou .csv"}), 400

        # Mapeamento das colunas (mantive seu original aqui!)
        mapa_colunas = {
            'Nome Completo': 'req_nome',
            'CPF': 'req_cpf',
            'RG': 'req_rg',
            'Telefone Principal': 'req_telefone',
            'E-mail': 'req_email',
            'Inscrição Imobiliária': 'inscricao_imobiliaria',
            'Logradouro do Imóvel': 'imovel_logradouro',
            'Número do Imóvel': 'imovel_numero',
            'Bairro do Imóvel': 'imovel_bairro',
            'Área Total do Lote (m²)': 'imovel_area_total',
            'Área Construída (m²)': 'imovel_area_construida',
            'Uso Principal do Imóvel': 'imovel_uso',
            'Padrão Construtivo': 'imovel_tipo_construcao',
            'Renda familiar mensal total (R$)': 'reurb_renda_familiar'
        }
        df.rename(columns=mapa_colunas, inplace=True)
        dados_para_db = df.to_dict(orient='records')

        for registro_dict in dados_para_db:
            modelo_columns = [c.name for c in CadastroReurb.__table__.columns]
            dados_filtrados = {key: value for key, value in registro_dict.items() if key in modelo_columns and pd.notna(value)}

            for campo in ['imovel_area_total', 'imovel_area_construida', 'reurb_renda_familiar']:
                if campo in dados_filtrados and (dados_filtrados[campo] == "" or pd.isna(dados_filtrados[campo])):
                    dados_filtrados[campo] = None

            novo_cadastro = CadastroReurb(**dados_filtrados)
            db.session.add(novo_cadastro)

        db.session.commit()
        return jsonify({"sucesso": True, "mensagem": f"{len(dados_para_db)} registros importados com sucesso!"}), 201

    except Exception as e:
        db.session.rollback()
        print("Erro ao importar:", str(e))  # 👈 log para debug
        return jsonify({"sucesso": False, "erro": f"Ocorreu um erro ao processar o arquivo: {str(e)}"}), 500


@app.route('/api/exportar', methods=['POST'])
def exportar_dados():
    try:
        colunas_selecionadas = request.json.get('colunas', [])
        if not colunas_selecionadas:
            # 👇 se não vier nada do frontend, pega todas as colunas do modelo
            colunas_selecionadas = [c.name for c in CadastroReurb.__table__.columns]

        cadastros = CadastroReurb.query.all()
        dados_para_exportar = []
        for cad in cadastros:
            registro = {col: getattr(cad, col, '') for col in colunas_selecionadas}
            dados_para_exportar.append(registro)

        if not dados_para_exportar:
            return jsonify({"sucesso": False, "erro": "Não há dados para exportar."}), 400

        df = pd.DataFrame(dados_para_exportar)

        mapa_nomes_amigaveis = {
            'req_nome': 'Nome Completo', 'req_cpf': 'CPF', 'req_rg': 'RG', 'req_telefone': 'Telefone',
            'req_email': 'E-mail', 'inscricao_imobiliaria': 'Inscrição Imobiliária',
            'imovel_logradouro': 'Logradouro', 'imovel_numero': 'Número', 'imovel_bairro': 'Bairro',
            'imovel_area_total': 'Área do Lote (m²)', 'imovel_area_construida': 'Área Construída (m²)',
            'reurb_renda_familiar': 'Renda Familiar (R$)', 'imovel_uso': 'Uso do Imóvel'
        }
        df.rename(columns=mapa_nomes_amigaveis, inplace=True)

        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Cadastros')
        output.seek(0)

        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='cadastros_reurb.xlsx'
        )

    except Exception as e:
        print("Erro ao exportar:", str(e))  # 👈 log para debug
        return jsonify({"sucesso": False, "erro": str(e)}), 500

# =======================================================================
# FIM: NOVAS ROTAS PARA IMPORTAÇÃO E EXPORTAÇÃO DE DADOS
# =======================================================================



# ▶️ Início do servidor (esta parte não é usada pelo Render, mas é boa para testes locais)
if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))